from app.web_cli import parse_command


def main():
    print("Welcome to OCRROO CLI. Type 'help' for a list of commands.")
    while True:
        command = input(">>>")
        if command.strip().lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        result = parse_command(command)
        print(result)


if __name__ == "__main__":
    main()
