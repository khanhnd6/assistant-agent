from langgraph.graph import START, StateGraph, MessagesState, END
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI


llm = ChatOpenAI(model = "gpt-4o-mini")

sys_msg = SystemMessage(content="You are helpful AI assistant")

def assistant(state: MessagesState):
    return {"messages": [llm.invoke([sys_msg] + state["messages"])]}

# build graph
builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)

builder.add_edge(START, "assistant")
builder.add_edge("assistant", END)

# compile graph
graph = builder.compile()
