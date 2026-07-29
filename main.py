from agent.agent import agent
from langchain_core.messages import HumanMessage


def main():

    print("Career Agent started.")
    print("Type 'exit' to quit.\n")

    app_config = {
        "configurable": {
            "thread_id": "user_1"
        }
    }

    while True:

        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        result = agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=user_input
                    )
                ]
            },
            config=app_config
        )

        last_message = result["messages"][-1]

        print(
            "\nAgent:",
            last_message.content,
            "\n"
        )


if __name__ == "__main__":
    main()
