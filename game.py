import sys
import random
import hashlib
import hmac
from typing import List, Tuple


class Dice:
    def __init__(self, faces: List[int]):
        if len(faces) != 6:
            raise ValueError("Each dice must have exactly 6 faces.")
        self.faces = faces

    def roll(self) -> int:
        return random.choice(self.faces)


class RandomGenerator:
    @staticmethod
    def generate_secure_random(bits: int = 256) -> bytes:
        return random.randbytes(bits // 8)

    @staticmethod
    def generate_random_int(range_max: int) -> int:
        while True:
            rand = int.from_bytes(RandomGenerator.generate_secure_random(256), 'big')
            if rand < (2**256 // range_max) * range_max:
                return rand % range_max

    @staticmethod
    def calculate_hmac(key: bytes, message: int) -> str:
        return hmac.new(key, str(message).encode(), hashlib.sha3_256).hexdigest()


class FairPlay:
    def __init__(self, range_max: int):
        self.range_max = range_max
        self.secret_key = RandomGenerator.generate_secure_random()
        self.computer_number = RandomGenerator.generate_random_int(range_max)
        self.hmac = RandomGenerator.calculate_hmac(self.secret_key, self.computer_number)

    def verify_and_get_result(self, user_number: int) -> Tuple[int, bytes]:
        result = (self.computer_number + user_number) % self.range_max
        return result, self.secret_key
class ProbabilityCalculator:
    @staticmethod
    def calculate_win_probabilities(dice_list: List[Dice]) -> List[List[float]]:
        n = len(dice_list)
        probabilities = [[0 for _ in range(n)] for _ in range(n)]

        for i in range(n):
            for j in range(n):
                if i != j:
                    win_count = 0
                    for face_i in dice_list[i].faces:
                        for face_j in dice_list[j].faces:
                            if face_i > face_j:
                                win_count += 1
                    probabilities[i][j] = win_count / 36  # 6x6 outcomes for each pair of dice
        return probabilities

class CLI:
    @staticmethod
    def display_help(dice_list: List[Dice]):
        probabilities = ProbabilityCalculator.calculate_win_probabilities(dice_list) # type: ignore
        n = len(dice_list)
        print("\nProbability Table (Row dice beats Column dice):")
        print("   " + " ".join([f"Dice {i}" for i in range(n)]))
        for i, row in enumerate(probabilities):
            print(f"Dice {i}: " + " ".join(f"{prob:.2f}" for prob in row))

    @staticmethod
    def display_error(message: str):
        print(f"Error: {message}")
        print("Usage: python game.py dice1,dice2,dice3,...")
        print("Each dice must have 6 comma-separated integers, e.g., 2,2,4,4,9,9.")


class DiceGame:
    def __init__(self, dice_config: List[str]):
        try:
            self.dice_list = [Dice(list(map(int, dice.split(",")))) for dice in dice_config]
        except ValueError as e:
            CLI.display_error(str(e))
            sys.exit(1)

    def start_game(self):
        fair_play = FairPlay(2)
        print(f"I selected a random value in the range 0..1 (HMAC={fair_play.hmac}).")
        user_input = input("Try to guess my selection (0 or 1): ")

        if user_input not in ["0", "1"]:
            print("Invalid input. Exiting.")
            sys.exit(1)

        user_number = int(user_input)
        result, key = fair_play.verify_and_get_result(user_number)
        print(f"My selection: {fair_play.computer_number} (KEY={key.hex()})")

        if result == 0:
            print("You make the first move!")
            self.user_turn_first = True
        else:
            print("I make the first move!")
            self.user_turn_first = False

        self.play_game()

    def play_game(self):
        available_dice = list(range(len(self.dice_list)))

        # Dice selection phase
        if self.user_turn_first:
            self.user_choose_dice(available_dice)
            self.computer_choose_dice(available_dice)
        else:
            self.computer_choose_dice(available_dice)
            self.user_choose_dice(available_dice)

        print("It's time for the game!")
        self.play_throws()

    def user_choose_dice(self, available_dice):
        print("Choose your dice:")
        for i in available_dice:
            print(f"{i} - {self.dice_list[i].faces}")

        while True:
            choice = input("Your selection: ")
            if choice.isdigit() and int(choice) in available_dice:
                chosen_dice = int(choice)
                print(f"You chose {self.dice_list[chosen_dice].faces}.")
                available_dice.remove(chosen_dice)
                return

            elif choice.lower() == "?":
                CLI.display_help(self.dice_list)
            elif choice.lower() == "x":
                print("Exiting game.")
                sys.exit(0)
            else:
                print("Invalid selection. Try again.")

    def computer_choose_dice(self, available_dice):
        chosen_dice = random.choice(available_dice)
        print(f"I choose {self.dice_list[chosen_dice].faces}.")
        available_dice.remove(chosen_dice)

    def play_throws(self):
        user_throw = self.get_throw("user")
        computer_throw = self.get_throw("computer")

        if user_throw > computer_throw:
            print(f"You win ({user_throw} > {computer_throw})!")
        elif user_throw < computer_throw:
            print(f"I win ({computer_throw} > {user_throw})!")
        else:
            print("It's a tie!")

    def get_throw(self, player: str) -> int:
        fair_play = FairPlay(6)
        print(f"I selected a random value in the range 0..5 (HMAC={fair_play.hmac}).")
        print("Add your number modulo 6.")
        print("0 - 0\n1 - 1\n2 - 2\n3 - 3\n4 - 4\n5 - 5\nX - exit\n? - help")

        while True:
            user_input = input("Your selection: ").strip().lower()
            if user_input == "x":
                print("Exiting game.")
                sys.exit(0)
            elif user_input == "?":
                CLI.display_help(self.dice_list)
            elif user_input in ["0", "1", "2", "3", "4", "5"]:
                break
            else:
                print("Invalid input. Please select a number between 0 and 5, or type '?' for help.")

        user_number = int(user_input)
        computer_number = fair_play.computer_number
        result = (user_number + computer_number) % 6
        print(f"My number is {computer_number} (KEY={fair_play.secret_key.hex()}).")
        print(f"The result is {computer_number} + {user_number} = {result} (mod 6).")

        # Simulate the dice roll based on the result
        throw = random.choice(self.dice_list[0 if player == "user" else 1].faces)
        print(f"{'Your' if player == "user" else 'My'} throw is {throw}.")
        return throw


if __name__ == "__main__":
    if len(sys.argv) < 4:
        CLI.display_error("At least 3 dice configurations are required.")
        sys.exit(1)

    game = DiceGame(sys.argv[1:])
    game.start_game()
