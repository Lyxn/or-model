# encoding=utf-8


def calc_compound_rate(interest, year):
    prop = (1 + interest) ** year
    return interest * prop / (prop - 1)


def main():
    rate = calc_compound_rate(0.15, 10)
    print(rate)


if __name__ == '__main__':
    main()
