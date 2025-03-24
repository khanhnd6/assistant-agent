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

async def filter_records(wrapper: RunContextWrapper[UserContext], args: str) -> str:
    try:
        parsed = FilterRecordSchema.model_validate_json(args)
        parsed = parsed.model_dump()
        mongodb_connection = MongoDBConnection()
        db = mongodb_connection.get_database()
        user_collection = db[f'{wrapper.context.user_id}_{parsed["collection"]}']
        query = convert_date(json.loads(parsed["pipeline"]))
        result = user_collection.aggregate(query)
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
    params_json_schema=PlotRecordsSchema.model_json_schema(),
    on_invoke_tool=plot_records,
)