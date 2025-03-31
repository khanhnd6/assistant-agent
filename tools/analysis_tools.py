from agents import FunctionTool, RunContextWrapper
from utils.context import UserContext, FilterRecordSchema, PlotRecordsSchema
from utils.database import MongoDBConnection
from utils.date import convert_date
import matplotlib.pyplot as plt
import json

async def plot_records(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed = PlotRecordsSchema.model_validate_json(args)
        parsed_dict = parsed.model_dump()
        parsed_dict["records"] = json.loads(parsed_dict["records"])
        chart_type = parsed_dict["chart_type"]
        x = parsed_dict["x"]
        y = parsed_dict["y"]
        hue = parsed_dict["hue"]
        data = parsed_dict["records"]
        x_vals = [d[x] for d in data] if x else None
        y_vals = [d[y] for d in data] if y else None
        hue_vals = [d[hue] for d in data] if hue else None
        plt.figure(figsize=(8, 5))
        if chart_type == "line":
            plt.plot(x_vals, y_vals, marker='o', linestyle='-')
            plt.title(f"Line Chart: {y} vs {x}")

        elif chart_type == "scatter":
            plt.scatter(x_vals, y_vals, c=hue_vals, cmap="viridis", alpha=0.7)
            plt.title(f"Scatter Plot: {y} vs {x}")

        elif chart_type == "bar":
            plt.bar(x_vals, y_vals)
            plt.title(f"Bar Chart: {y} vs {x}")

        elif chart_type == "hist":
            plt.hist(x_vals, bins="auto", alpha=0.7, color='blue', edgecolor='black')
            plt.title(f"Histogram of {x}")

        elif chart_type == "box":
            plt.boxplot(y_vals, vert=True)
            plt.title(f"Box Plot: {y}")

        else:
            print(f"Loại biểu đồ '{chart_type}' không được hỗ trợ!")
            return

        plt.xlabel(x if x else "")
        plt.ylabel(y if y else "")
        file_name = "image.jpg"
        plt.savefig(file_name)
        plt.close()
        return 'SUCCESS'
    except Exception as e:
        print('Error', e)

# async def filter_records(wrapper: RunContextWrapper[UserContext], args: str) -> str:
#     try:
#         parsed = FilterRecordSchema.model_validate_json(args)
#         parsed = parsed.model_dump()
#         mongodb_connection = MongoDBConnection()
#         db = mongodb_connection.get_database()
#         user_collection = db[f'{wrapper.context.user_id}_{parsed["collection"]}']
#         query = convert_date(json.loads(parsed["pipeline"]))
#         result = user_collection.aggregate(query)
#         mongodb_connection.close_connection() 
#         return str(list(result))
#     except Exception as e:
#         return f'Error'



async def filter_records(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed_data = FilterRecordSchema.model_validate_json(args)
        parsed_data = parsed_data.model_dump()
        
        user_id = wrapper.context.user_id
        
        pipeline = parsed_data["pipeline"]
        pipeline = json.loads(pipeline) if pipeline else []
        schema_name = parsed_data["collection"]
        
        pipeline = convert_date(pipeline)
                
        is_set_condition = False
        additional_condition = {
            "_user_id": user_id,
            "_schema_name": schema_name
        }
        
        for stage in pipeline:
            if "$match" in stage:
                
                if "_deleted" in stage["$match"]:
                    deleted = stage["$match"]["_deleted"]
                    additional_condition["_deleted"] = deleted if isinstance(deleted, bool) else (deleted == 1)
                    
                stage["$match"].update(additional_condition)
                is_set_condition = True
                break
        
        if not is_set_condition:
            pipeline.insert(0, {
                "$match": {
                    "_user_id": user_id,
                    "_schema_name": schema_name
                }
            })
        
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        user_collection = db['RECORDS']
        
        results = list(user_collection.aggregate(pipeline))
        mongodb_connection.close_connection()
        
        print(pipeline)
        
        return str(results)
    except Exception as e:
        return f"Error in retrieving data - {e}"
    
# filter_records_tool = FunctionTool(
#     name="filter_records_tool",
#     description="""
#         This tool retrieves records from the specified collection based on filter criteria.
#         It takes a defined pipeline JSON array and a schema name to query the database and return result
#     """,
#     params_json_schema=FilterRecordSchema.model_json_schema(),
#     on_invoke_tool=filter_records,
# )


filter_records_tool = FunctionTool(
    name="filter_records_tool",
    description="""
This tool accepts only data structure like this:
{
    "pipeline": "JSON array of object to filterring data",
    "collection": "The name of schema"
}

**Note**:
    - The record data is an object with the structure like this:
    {
      "<field1>": "<value1>",
      "<datetime field2>": <datetime>,
      "<field3>": <value3>,
      "<additional field>": <additional value>, // that not in fields of schema
      "_user_id": "<user id>",
      "_record_id": "<record id>",
      "_deleted": False,
      "_send_notification_at": <datetime> // datetime or null if the record is no need to send notification to user
    }
    
    - Based on data structure like that, this tool's is used to query data from MongoDB, it accepts `pipeline` to retrieve data, aggregation,...
    - `collection` is REAL schema name.
    - Do NOT filter by `_record_id`, `_user_id`, just only by `_schema_name`, fields of schema, `_deleted` (the flag whether it is deleted or not, if True passing 1 else passing 0), `_send_notification_at` (datetime that record will be reminded to user).
    - Data is an object based on fields of schema, filter by it based on REAL field name and data type
    - Notice that if field type is datetime, passing value in ISO formatted string.
    """,
    params_json_schema=FilterRecordSchema.model_json_schema(),
    on_invoke_tool=filter_records,
)

plot_records_tool = FunctionTool(
    name="plot_records_tool",
    description="""
        Generates various types of charts (line, scatter, bar, histogram, box) from input data.
        It returns a file path to the generated chart image.
    """,
    params_json_schema=PlotRecordsSchema.model_json_schema(),
    on_invoke_tool=plot_records,
)