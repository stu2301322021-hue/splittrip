def main():
    while True:
        print("\nSplitTrip")
        print("Планиране на пътувания и общи разходи")
        print("0. Изход")

        choice = input("Избор: ").strip()

        if choice == "0":
            print("До скоро!")
            return

        print("Невалиден избор. Опитай отново.")


if __name__ == "__main__":
    main()