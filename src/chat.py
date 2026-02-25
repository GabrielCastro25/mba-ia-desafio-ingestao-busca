from search import search_prompt


def main():
    chain = search_prompt()

    if not chain:
        print("Não foi possível iniciar o chat. Verifique os erros de inicialização.")
        return

    print("Chat iniciado. Digite 'sair' para encerrar.\n")

    while True:
        question = input("PERGUNTA: ").strip()

        if not question:
            continue

        if question.lower() in ("sair", "exit", "quit"):
            break

        answer = chain(question)
        print(f"RESPOSTA: {answer}\n")


if __name__ == "__main__":
    main()
