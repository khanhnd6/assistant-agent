from agents import FunctionTool, RunContextWrapper
from utils.context import UserContext, FilterRecordSchema, PlotSchema
from utils.database import MongoDBConnection
import matplotlib.pyplot as plt
import json

async def plot_records(args: str) -> str:
    try:
        parsed = PlotSchema.model_validate_json(args)
        parsed_dict = parsed.model_dump()
        chart_type = parsed_dict["chart_type"]
        data = parsed_dict["data"]
        x = parsed_dict["x"]
        y = parsed_dict["y"]
        hue = parsed_dict["hue"]
        print(type(chart_type))
        # bins = parsed_dict["bins"]
        # x_vals = [d[x] for d in data] if x else None
        # y_vals = [d[y] for d in data] if y else None
        # hue_vals = [d[hue] for d in data] if hue else None
        # plt.figure(figsize=(8, 5))
        # if chart_type == "line":
        #     plt.plot(x_vals, y_vals, marker='o', linestyle='-')
        #     plt.title(f"Line Chart: {y} vs {x}")

        # elif chart_type == "scatter":
        #     plt.scatter(x_vals, y_vals, c=hue_vals, cmap="viridis", alpha=0.7)
        #     plt.title(f"Scatter Plot: {y} vs {x}")

        # elif chart_type == "bar":
        #     plt.bar(x_vals, y_vals)
        #     plt.title(f"Bar Chart: {y} vs {x}")

        # elif chart_type == "hist":
        #     plt.hist(x_vals, bins=bins, alpha=0.7, color='blue', edgecolor='black')
        #     plt.title(f"Histogram of {x}")

        # elif chart_type == "box":
        #     plt.boxplot(y_vals, vert=True)
        #     plt.title(f"Box Plot: {y}")

        # else:
        #     print(f"Loại biểu đồ '{chart_type}' không được hỗ trợ!")
        #     return

        # plt.xlabel(x if x else "")
        # plt.ylabel(y if y else "")
        # file_name = f"chart.png"
        # plt.savefig(file_name)
        # plt.close()
        return 'Success'
    except Exception as e:
        print('Error')

async def filter_records(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed = FilterRecordSchema.model_validate_json(args)
        parsed = parsed.model_dump()
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        user_collection = db[f'{wrapper.context.user_id}_{parsed["collection"]}']
        print(json.loads(parsed["pipeline"]))
        result = user_collection.aggregate(json.loads(parsed["pipeline"]))
        mongodb_connection.close_connection() 
        return str(list(result))
    except Exception as e:
        return f'Error'
    
filter_records_tool = FunctionTool(
    name="filter_records_tool",
    description="""
        This tool retrieves records from the specified collection based on filter criteria.
        It takes a defined pipeline JSON array and a schema name to query the database and return result
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
    params_json_schema=PlotSchema.model_json_schema(),
    on_invoke_tool=plot_records,
)
