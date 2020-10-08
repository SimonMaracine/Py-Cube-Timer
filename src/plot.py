import matplotlib.pyplot as plt

from src.session import SessionData


def plot(session_data: SessionData):
    plt.figure().canvas.set_window_title("Statistics")  # This might be wrong, I'm not sure

    solve_indices = [i for i in range(len(session_data.solves))]
    times = session_data.solves
    plt.plot(solve_indices, times, label="single", color="gray")

    ao5 = session_data.all_ao5
    if ao5:  # If it's not empty
        indices = [i + 5 for i in range(len(ao5))]
        plt.plot(indices, ao5, label="ao5", color="blue")

    ao12 = session_data.all_ao12
    if ao12:  # If it's not empty
        indices = [i + 12 for i in range(len(ao12))]
        plt.plot(indices, ao12, label="ao12", color="red")

    plt.xlabel("solve index")
    plt.ylabel("solve time (s)")
    plt.title(session_data.name)
    plt.grid()

    plt.legend()
    plt.show()
