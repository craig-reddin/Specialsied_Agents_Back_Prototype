import matplotlib.pyplot as plt
import time
import random

def insertion_sort(arr):
    # Traverse through 1 to len(arr)
    for i in range(1, len(arr)):
        key = arr[i]
        # Move elements of arr[0..i-1], that are greater than key,
        # to one position ahead of their current position
        j = i - 1
        while j >= 0 and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key

def measure_time(arr):
    start_time = time.time()
    insertion_sort(arr)
    end_time = time.time()
    return end_time - start_time

# Generate data for plotting
input_sizes = [10, 50, 100, 200, 500, 1000, 2000, 5000]
times = []

for size in input_sizes:
    arr = [random.randint(0, 10000) for _ in range(size)]
    time_taken = measure_time(arr)
    times.append(time_taken)

# Plotting the line chart
plt.figure(figsize=(10, 6))
plt.plot(input_sizes, times, marker='o')
plt.title('Insertion Sort Time Complexity')
plt.xlabel('Input Size')
plt.ylabel('Time (seconds)')
plt.grid(True)
plt.show()