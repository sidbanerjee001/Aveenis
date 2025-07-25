# This file is for data processing related queries. No backend/frontend integration, keep all API calls and whatever
# out of this.

from math import sqrt


def update_ticker_data_today(score: int, data: list) -> list:
    # incomplete data case, on init or perhaps data flush
    if len(data) < 24:
        return data + [score]

    # regular case (full 24hrs)
    data.pop(0)
    return data + [score]


def update_ticker_data_history(score: int, expiry: int, data: list) -> list:

    # Flushes if at max capacity OR we update expiry to a lower value (i.e. 1 month -> 14 days)
    if len(data) >= expiry:
        while len(data) >= expiry:
            data.pop(0)

    return data + [score]


def calculate_interval_change(data: list, interval: int) -> float:
    if len(data) < interval + 1 or data[-1 - interval] == 0:
        return float("-inf")

    prev = data[-1 - interval]
    return (data[-1] - prev) / prev  # between 0 - 1, * 100 for %


def calculate_accel(data: list, interval: int) -> float:
    if (
        len(data) < (interval * 2) + 1
        or data[-1 - interval] == 0
        or data[-1 - (2 * interval)] == 0
    ):
        return float("-inf")

    return calculate_interval_change(data, interval) - calculate_interval_change(
        data[: len(data) - interval], interval
    )


def calculate_accels(data) -> list:
    accels = []
    for i in range((2), len(data)):
        sub_data = data[:i+1]
        accel = calculate_accel(sub_data, 1)
        
        if accel == float('inf') or accel == -float('inf'):
            accel = 0
        elif accel == float('nan'):
            accel = 0

        accels.append(accel)
        
    return accels

def calculate_function(data: list) -> float:
    raw_score = sqrt(data[0]) + data[1]
    return round(raw_score, 3)


# Test cases
def tests():

    # format: each c in case is a tuple:
    # (Debugging output, function to call, list of tuples of test cases ((comma,separated,function,parameters), expected_output))
    cases = (
        (
            "Testing update ticker today...",
            update_ticker_data_today,  # f(score, data)
            [
                ((5, [1, 2, 3, 4]), [1, 2, 3, 4, 5]),
                ((5, []), [5]),
                (
                    (
                        2,
                        [
                            1,
                            2,
                            3,
                            4,
                            5,
                            6,
                            7,
                            8,
                            9,
                            10,
                            11,
                            12,
                            13,
                            14,
                            15,
                            16,
                            17,
                            18,
                            19,
                            20,
                            21,
                            22,
                            23,
                            24,
                        ],
                    ),
                    [
                        2,
                        3,
                        4,
                        5,
                        6,
                        7,
                        8,
                        9,
                        10,
                        11,
                        12,
                        13,
                        14,
                        15,
                        16,
                        17,
                        18,
                        19,
                        20,
                        21,
                        22,
                        23,
                        24,
                        2,
                    ],
                ),
            ],
        ),
        (
            "Testing update ticker history...",
            update_ticker_data_history,  # f(score, expiry, data)
            [
                ((5, 2, [1]), [1, 5]),
                ((5, 2, [1, 2]), [2, 5]),
                ((5, 2, [1, 2, 3]), [3, 5]),
            ],
        ),
        (
            "Testing interval calculation...",
            calculate_interval_change,  # f(data, interval)
            [
                (([1, 2, 3, 4, 5], 1), 0.25),
                (([1, 2, 3, 4, 5], 2), 2 / 3),
                (([1, 2, 3, 5, 4], 1), -0.2),
                (([1, 2], 2), float("-inf")),
                (([], 1), float("-inf")),
            ],
        ),
    )

    for c in cases:
        print(c[0])
        f = c[1]
        p = True
        for case in c[2]:
            exp = case[1]
            got = f(*case[0])
            if exp != got:
                print("Test failed. Expected", exp, "but got", got)
                p = False
        if p:
            print("All tests passed!")
