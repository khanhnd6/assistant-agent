from utils.date import convert_to_local_timezone, current_time_v3, convert_date_v2
from group.context_tool import retrieve_struct_schemas, retrieve_brief_schemas
from agents import RunContextWrapper, Agent, FunctionTool
from group.prompt import STANDALONE_PREFIX_PROMPT
from utils.database import MongoDBConnection
from group.record.record_context import *
from utils.context import UserContext
from utils.data_extensions import *
import ujson as json
import uuid

async def dynamic_action_agent_instruction(wrapper: RunContextWrapper[UserContext], agent: Agent[UserContext]) -> str:
    profile = wrapper.context.user_profile
    current = current_time_v3(profile["timezone"]) if profile else current_time_v3()
    instruction = f"""
    {STANDALONE_PREFIX_PROMPT}
    ### Nhiệm vụ của bạn

    Bạn là người thực hiện công việc theo mô tả job brief. Job brief sẽ gồm các trường: schema_name, action, request.
    Trong lúc thực hiện, NGHIÊM CẤM hỏi hay yêu cầu xác nhận từ người dùng. Khi thực hiện xong, báo lại kết quả của bạn.

    1. Đầu tiên, gọi `retrieve_records_tool` ĐÚNG 1 LẦN DUY NHẤT với schema_name, để:
       - Nếu tool trả về không có dữ liệu thì dừng lại, không được gọi nữa. Tóm lại chỉ gọi đúng 1 lần duy nhất
       - Kiểm tra xem đã có dữ liệu y hệt hoặc lặp lại chưa. Nếu có thì cấm tạo mới, chỉ lấy ra record_id.
       - (Nếu cần) Lấy ra record_id của dòng dữ liệu đang cần update hoặc delete
       - Nhìn để hiểu cấu trúc dữ liệu khi chuẩn bị tạo dòng dữ liệu mới 

    2. Lấy ra cấu trúc của `schema_name` trong danh sách sau: `{retrieve_struct_schemas(wrapper)}`, phục vụ action = create hoặc action = update
       
    3. Khi action = create:
    - Chuẩn bị đầu vào cẩn thận, chính xác theo yêu cầu của `create_record_tool`. NGHIÊM CẤM gọi mà không truyền gì.
    - Nếu trong yêu cầu có đi kèm "lời nhắc nhở từ người dùng" hoặc "có khả năng cần nhắc nhở", nhớ tạo giá trị \
      datetime hợp lí ISO-8601 với múi giờ UTC cho trường `send_notification_at`
      VD: ghi chú: ăn tối lúc 6h tối -> bạn biết nên đặt send_notification_at vào 18h tối hôm nay
      Thêm vào phản hồi rằng bạn sẽ nhắc nhở vào giờ đó (không cần nhắc tới múi giờ)
    - Nếu trường thời gian cần lấy thời gian hiện tại, xem xét thời gian ở đây: {current}.
      VD: ăn tối sau 2 phút nữa, lấy thời gian {current} xong cộng thêm 2 phút

    3. Khi action = update:
    - Từ record_id đã phát hiện ra ở trên, chuẩn bị đầu vào cẩn thận, chính xác theo yêu cầu của `update_record_tool`
    - Nếu người dùng yêu cầu nhắc nhở bản ghi này, cập nhật giá trị datetime ISO-8601 với múi giờ UTC cho trường `send_notification_at` \
      Tự động nhắc nhở đúng theo nội dung và yêu cầu, bạn không được đặt datetime sớm hơn hoặc muộn hơn (trừ phi người dùng muốn)
      Thêm vào phản hồi rằng bạn sẽ nhắc nhở vào giờ đó (không cần nhắc tới múi giờ)

    4. Khi action = delete:
    - Lấy ra record_id tìm được ở bước 1 và schema_name đầu vào, chuẩn bị đầu vào cho hàm `delete_record_tool`
    """
    return instruction

async def dynamic_record_agent_instruction(wrapper: RunContextWrapper[UserContext], agent: Agent[UserContext]) -> str:
    instruction = f"""
    ### Nhiệm vụ của bạn

    Bạn sẽ phân tích yêu cầu của người dùng, từ đó định nghĩa ra các nhiệm vụ giao cho công cụ khác thực hiện.
    Trước hết, bạn được cung cấp các schema cần thiết: {retrieve_brief_schemas(wrapper)}. Dữ liệu người dùng định CRUD sẽ dựa theo schema này.
    Đầu tiên, đọc kĩ yêu cầu người dùng, giả dụ họ nói "tạo ghi chú ăn tối 6PM và ăn sáng 2AM", bạn tự biết bạn có tận 2 nhiệm vụ.

    Đối với mỗi nhiệm vụ, nó có format như sau: `schema_name`:giá trị, `action`: giá trị, `request`: giá trị 
    Để có thể lấy được giá trị cho format, bạn cần làm từng bước sau:
    1. `schema_name`: Xem trên các schema được cung cấp có cái nào liên quan, gần giống với yêu cầu người dùng không?
       VD: Tôi muốn lập kế hoạch -> tìm schema có tên `kế hoạch` hoặc `plan` trong {retrieve_brief_schemas(wrapper)}
       Nếu thực sự không tìm được, hãy tự nghĩ ra schema name rồi gọi `create_schema_tool` DUY NHẤT 1 LẦN và đợi kết quả trước khi sang bước tiếp theo.
    2.`action`: Xem người dùng muốn làm gì (create/update/delete).
    3. `request`: viết lại mô tả nhiệm vụ vào trường này và giải thích kĩ cho công cụ có thể hiểu việc cần làm
    4. Truyền format trên kèm giá trị bạn vừa có được vào `action_record_tool` để nó thực hiện nhiệm vụ, và trả về đúng kết quả của hàm đó
    """
    return instruction

async def create_records(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed = DataEntry.model_validate_json(args)
        parsed_data = parsed.model_dump()
        
        user_id = wrapper.context.user_id
        
        data = json.loads(parsed_data['data'])
        
        data["_user_id"] = user_id
        data["_record_id"] = str(uuid.uuid4()) 
        data["_schema_name"] = parsed_data["schema_name"]
        data["_send_notification_at"] = parsed_data["send_notification_at"]
        data["_deleted"] = False
        
        profile = wrapper.context.user_profile
        timezone = profile["timezone"] if profile else "Asia/Ho_Chi_Minh"
        data = convert_date_v2(data, timezone)
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        user_collection = db['RECORDS']
        
        result = user_collection.insert_one(data)
        mongodb_connection.close_connection() 
        
        return f'Success, Data: {data}'
    except Exception as e:
        return f'Error {str(e)}'

create_record_tool = FunctionTool(
    name="create_record_tool",
    description="""
        This tool creates a new record in the specified collection. Call this tool once for each different item
        It only accepts data in the following structure:
        {
            "schema_name": "The real name of the schema, not `display_name`",
            "data": { 
                // JSON data that follows the fields of the selected schema 
                // fields of schema are required
                // Additional information is allowed, optional
            },
            "send_notification_at": "<datetime> in ISO formatted string"
        }
        Notes:
        `schema_name`: the REAL name of the schema this record belongs to, not `display_name`.
        `data`: Main record data based on schema fields, keys are REAL field name, not `display_name` of the schema
        `send_notification_at`: Optional. If the user wants a reminder, otherwise leave it empty or null.
        
        Allow to call in parallel with different ones
    """,
    params_json_schema=DataEntry.model_json_schema(),
    on_invoke_tool=create_records,
    strict_json_schema=True
)

async def retrieve_records(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed_data = SchemaNameInput.model_validate_json(args)
        parsed_data = parsed_data.model_dump()
        user_id = wrapper.context.user_id
        
        schema_name = parsed_data["schema_real_name"]
        
        query = {
            "_user_id": user_id,
            "_schema_name": schema_name,
            "_deleted": False
        }
        
        projection = {
            "_id": 0,
            "_user_id": 0,
            "_deleted": 0
        }
        
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        collection = db['RECORDS']
        
        records = list(collection.find(query, projection))

        mongodb_connection.close_connection()

        profile = wrapper.context.user_profile
        timezone = profile["timezone"] if profile else "Asia/Ho_Chi_Minh"
        records = convert_to_local_timezone(records, timezone)        
        records = remove_first_underscore(records)
        records = remove_empty_values(records)
        return str(records) if records else "This schema has no data yet. Agent please stop calling this tool!"
    except Exception as e:
        return f"Error in retrieving data - {e}"

retrieve_records_tool = FunctionTool(
    name="retrieve_records_tool",
    description="""
   You can just use this tool if you got a schema_name.
   This tool will return data of target schema and accepts only data structure like this:
   {
      "schema_name": "The REAL name of the schema, not `display_name`"
   }
   """,
    params_json_schema=SchemaNameInput.model_json_schema(),
    on_invoke_tool=retrieve_records
)

async def delete_record(wrapper: RunContextWrapper[UserContext], args: str) -> str: 
    try:
        parsed_obj = DeletedRecordInput.model_validate_json(args)
        parsed_obj = parsed_obj.model_dump()
        
        user_id = wrapper.context.user_id
        record_id, schema_name = parsed_obj["record_id"], parsed_obj["schema_real_name"]
        
        context_schemas = wrapper.context.schemas
        
        if schema_name not in [schema["name"] for schema in context_schemas]:
            return f"Not found {schema_name}"
        
        db_connection = MongoDBConnection()
        db = db_connection.get_database()
        collection = db["RECORDS"]
        
        delete_result = collection.update_one({"_record_id": record_id, "_user_id": user_id, "_schema_name": schema_name}, {"$set": {"_deleted": True}})
        db_connection.close_connection()
        
        deleted_rows = delete_result.modified_count
        
        if deleted_rows <= 0:
            return "Not found that row matching with provided `record_id` or `schema_name` based on user"
        
        return "Success"
    except Exception as e:
        return f"Error happen - {str(e)}"

delete_record_tool = FunctionTool(
    name="delete_record_tool",
    description="""
    This tool is called to delete 1 row of data only based on `schema_name` and `record_id`, it accepts a JSON data structure like:
    {
        "record_id": "The record ID of data record, that is `_record_id`",
        "schema_name": "The REAL unique schema's name, not `display_name`"
    }
    """,
    params_json_schema=DeletedRecordInput.model_json_schema(),
    on_invoke_tool=delete_record,
    strict_json_schema=True
)

async def update_record(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed_obj = DataEntry.model_validate_json(args)
        parsed_obj = parsed_obj.model_dump()
        user_id = wrapper.context.user_id
        data = json.loads(parsed_obj['data'])
        
        schema_name = parsed_obj["schema_name"]
        record_id = parsed_obj["record_id"]
        
        data["_user_id"] = user_id
        data["_record_id"] = record_id
        data["_schema_name"] = schema_name
        
        if parsed_obj["send_notification_at"]:
            data["_send_notification_at"] = parsed_obj["send_notification_at"]
          
        profile = wrapper.context.user_profile
        timezone = profile["timezone"] if profile else "Asia/Ho_Chi_Minh"
        data = convert_date_v2(data, timezone)
        
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        collection = db['RECORDS']
        
        result = collection.update_one({ "_record_id": record_id, "_user_id": user_id, "_schema_name": schema_name}, {"$set": data})
        
        mongodb_connection.close_connection() 
        
        if result.modified_count <= 0:
            return "No data is modified"
        
        return f'Success: {data}'
    except Exception as e:
        return f"Error happened - {e}"

update_record_tool = FunctionTool(
    name="update_record_tool",
    description="""
        This tool is used to update existing record of data, it takes in a JSON input with structure:
        {
            "schema_name": <The REAL schema's name>,
            "record_id": <Record ID>,
            "data": <JSON object of data of schema's fields only>,
            "send_notification_at": <Datetime to reminder/send a notification for this record in ISO format>,
            "deleted": <The flag to indicate whether the data is deleted or not, passing 1 if True, else passing 0>
        }
        Remember that only passing **changed fields**
        
        Notes:
        `schema_name`: required, the REAL name of the schema this record belongs to, not `display_name`.
        
        "record_id": required, refer to `_record_id` or `record_id` of data

        `data`: required, Main changed record data based on schema fields, keys are REAL field name, not `display_name` of the schema

        `send_notification_at`: Optional. If the user wants a reminder, otherwise leave it empty or null.
        
        `deleted`: required, "The flag to indicate whether the data is deleted or not, passing 1 if True, else passing 0"
        
        Reflect carefully to fill the data
        Do NOT store duplicated data.
    """,
    params_json_schema=DataEntry.model_json_schema(),
    on_invoke_tool=update_record,
    strict_json_schema=True
)