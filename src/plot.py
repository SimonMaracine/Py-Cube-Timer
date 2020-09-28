import matplotlib.pyplot as plt

from src.session import SessionData


def plot(session_data: SessionData):
    solve_indices = [i for i in range(len(session_data.solves))]
    times = session_data.solves

    fig, ax = plt.subplots()
    ax.plot(solve_indices, times)

    ax.set(xlabel="solve index", ylabel="solve time (s)", title=session_data.name)
    ax.grid()

    plt.show()
