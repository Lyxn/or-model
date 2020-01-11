import numpy as np
from scipy.optimize import linprog


def is_zero(a, eps=1e-6):
    return -eps <= a <= eps


def fmt_array(arr, fmt="%.3f"):
    return [fmt % x for x in arr]


def str_array(arr, sep="\t", fmt="%.3f"):
    return sep.join(fmt_array(arr, fmt))


def run():
    # Context
    garage_name = ["Winchester", "Andover", "Basingstoke", "Poole", "Woking",
                   "Newbury", "Portsmouth", "Alresford", "Salisbury", "Guilford",
                   "Alton", "Weybridge", "Dorchester", "Bridport", "Weymouth",
                   "Portland", "Chichester", "Petersfield", "Petworth", "Midhurst",
                   "Reading", "Southampton", "Bournemouth", "Henley", "Maidenhead",
                   "Fareham", "Romsey", "Ringwood"]
    input_name = ["Staff", "Show room space",
                  "Population in category 1", "Population in category 2",
                  "Enquiries Alpha model", "Enquiries Beta model", ]
    output_name = ["Alpha", "Beta", "Profit"]
    garage_matrix = np.array([
        [7, 8, 10, 12, 8.5, 4, 2, 0.6, 1.5],
        [6, 6, 20, 30, 9, 4.5, 2.3, 0.7, 1.6],
        [2, 3, 40, 40, 2, 1.5, 0.8, 0.25, 0.5],
        [14, 9, 20, 25, 10, 6, 2.6, 0.86, 1.9],
        [10, 9, 10, 10, 11, 5, 2.4, 1, 2],
        [24, 15, 15, 13, 25, 1.9, 8, 2.6, 4.5],
        [6, 7, 50, 40, 8.5, 3, 2.5, 0.9, 1.6],
        [8, 7.5, 5, 8, 9, 4, 2.1, 0.85, 2],
        [5, 5, 10, 10, 5, 2.5, 2, 0.65, 0.9],
        [8, 10, 30, 35, 9.5, 4.5, 2.05, 0.75, 1.7],
        [7, 8, 7, 8, 3, 2, 1.9, 0.70, 0.5],
        [5, 6.5, 9, 12, 8, 4.5, 1.8, 0.63, 1.4],
        [6, 7.5, 10, 10, 7.5, 4, 1.5, 0.45, 1.45],
        [11, 8, 8, 10, 10, 6, 2.2, 0.65, 2.2],
        [4, 5, 10, 10, 7.5, 3.5, 1.8, 0.62, 1.6],
        [3, 3.5, 3, 20, 2, 1.5, 0.9, 0.35, 0.5],
        [5, 5.5, 8, 10, 7, 3.5, 1.2, 0.45, 1.3],
        [21, 12, 6, 6, 15, 8, 6, 0.25, 2.9],
        [6, 5.5, 2, 2, 8, 5, 1.5, 0.55, 1.55],
        [3, 3.6, 3, 3, 2.5, 1.5, 0.8, 0.20, 0.45],
        [30, 29, 120, 80, 35, 20, 7, 2.5, 8],
        [25, 16, 110, 80, 27, 12, 6.5, 3.5, 5.4],
        [19, 10, 90, 22, 25, 13, 5.5, 3.1, 4.5],
        [7, 6, 5, 7, 8.5, 4.5, 1.2, 0.48, 2],
        [12, 8, 7, 10, 12, 7, 4.5, 2, 2.3],
        [4, 6, 1, 1, 7.5, 3.5, 1.1, 0.48, 1.7],
        [2, 2.5, 1, 1, 2.5, 1, 0.4, 0.1, 0.55],
        [2, 3.5, 2, 2, 1.9, 1.2, 0.3, 0.09, 0.4]
    ])
    num_garages = len(garage_name)
    num_inputs = len(input_name)
    num_outputs = len(output_name)
    garage_inputs = garage_matrix[:, 0:num_inputs]
    garage_outputs = garage_matrix[:, num_inputs:]

    def check_garage(idx):
        obj_input = garage_inputs[idx]
        obj_output = garage_outputs[idx]
        inputs = np.delete(garage_inputs, idx, axis=0)
        outputs = np.delete(garage_outputs, idx, axis=0)
        ret = optimize_efficiency(obj_input, obj_output, inputs, outputs)
        if ret.status != 0:
            print("%d %s is efficient." % (idx, garage_name[idx]))
        else:
            print("%d %s is not efficient." % (idx, garage_name[idx]))
            # print("efficient ratio %f" % (1 / abs(ret.fun)))
            x_garage = ret.x[:num_garages - 1]
            nnz_idx = [i for i in range(len(x_garage)) if not is_zero(x_garage[i])]
            g_name = [garage_name[i] if i < idx else garage_name[i + 1] for i in nnz_idx]
            print("Comparators")
            print("\t".join(g_name))
            print(str_array(x_garage[nnz_idx], fmt="%.6f"))
            print("\t".join(output_name))
            print(str_array(obj_output))
            print(str_array(x_garage.dot(outputs)))
        print()

    for j in range(num_garages):
        check_garage(j)
        # break


def optimize_efficiency(obj_input, obj_output, inputs, outputs):
    # Variable
    num_row = len(inputs)
    num_input = len(obj_input)
    num_output = len(obj_output)

    def optimize0():
        a_in = inputs.T
        a_out = -outputs.T
        a_ub = np.concatenate([a_in, a_out], axis=0)
        b_ub = np.concatenate([obj_input, -obj_output], axis=0)
        c = a_out[2]
        # return linprog(c, A_eq=a_in, b_eq=obj_input, A_ub=a_out, b_ub=-obj_output)
        return linprog(c, A_ub=a_ub, b_ub=b_ub)

    def optimize1():
        num_var = num_row + 1
        c = np.zeros(num_var)
        c[-1] = -1
        a_in = np.concatenate([inputs.T, np.zeros([num_input, 1])], axis=1)
        a_out = np.concatenate([-outputs.T, np.reshape(obj_output, (num_output, 1))], axis=1)
        a_ub = np.concatenate([a_in, a_out], axis=0)
        b_ub = np.concatenate([obj_input, np.zeros(num_output)], axis=0)
        bounds = [(0, None)] * num_row + [(1, None)]
        return linprog(c, A_ub=a_ub, b_ub=b_ub, bounds=bounds, method="revised simplex")

    def print_result():
        print(ret)
        if ret.status == 0:
            x = ret.x[:num_row]
            print(str_array(obj_input))
            print(str_array(inputs.T.dot(x)))
            print(str_array(obj_output))
            print(str_array(outputs.T.dot(x)))

    ret = optimize1()
    print_result()

    return ret


if __name__ == '__main__':
    run()
