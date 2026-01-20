#!/usr/bin/env python3
"""
Simple FizzBuzz app
Prints numbers from 1 to 100, replacing:
- Multiples of 3 with "Fizz"
- Multiples of 5 with "Buzz"
- Multiples of both 3 and 5 with "FizzBuzz"
"""

def fizzbuzz(n):
    """
    Generate FizzBuzz sequence up to n
    
    Args:
        n (int): Upper limit for the sequence
    
    Returns:
        list: FizzBuzz sequence
    """
    result = []
    for i in range(1, n + 1):
        if i % 15 == 0:
            result.append("FizzBuzz")
        elif i % 3 == 0:
            result.append("Fizz")
        elif i % 5 == 0:
            result.append("Buzz")
        else:
            result.append(str(i))
    return result

def main():
    """Main function to run the FizzBuzz app"""
    print("FizzBuzz App")
    print("=" * 50)
    
    # Get user input for upper limit
    try:
        n = int(input("Enter the upper limit (default 100): ") or 100)
        if n < 1:
            print("Please enter a positive integer.")
            return
    except ValueError:
        print("Invalid input. Using default value 100.")
        n = 100
    
    # Generate and print FizzBuzz sequence
    sequence = fizzbuzz(n)
    for item in sequence:
        print(item)

if __name__ == "__main__":
    main()