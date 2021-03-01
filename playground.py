from simulation_modes import test_mode
import os
# from experiments import plotting
from metrics import anonymity_metrics, performance_metrics
from classes.Utilities import get_total_num_of_target_packets
import pandas as pd
import shutil
import json

if __name__ == "__main__":

    # try:

    print("Mix-network Simulator\n")
    print("Insert the following network parameters to test: ")

    with open('test_config.json') as json_file:
        config = json.load(json_file)

    if not os.path.exists('./playground_experiment/logs'):
        os.makedirs('./playground_experiment/logs')
    else:
        try:
            os.remove('./playground_experiment/logs/packet_log.csv')
            os.remove('./playground_experiment/logs/message_log.csv')
            os.remove('./playground_experiment/logs/last_mix_entropy.csv')
        except:
            pass

    test_mode.run(exp_dir='playground_experiment', conf_file=None, conf_dic=config)
    pps = test_mode.throughput

    packetLogsDir = './playground_experiment/logs/packet_log.csv'
    messageLogsDir = './playground_experiment/logs/message_log.csv'
    entropyLogsDir = './playground_experiment/logs/last_mix_entropy.csv'
    packetLogs = pd.read_csv(packetLogsDir, delimiter=';')
    messageLogs = pd.read_csv(messageLogsDir, delimiter=';')
    entropyLogs = pd.read_csv(entropyLogsDir, delimiter=';')

    unlinkability = anonymity_metrics.getUnlinkability(packetLogs)
    throughput = performance_metrics.computeThroughput(messageLogs)
    entropy = anonymity_metrics.getEntropy(entropyLogs, get_total_num_of_target_packets(config))
    latency = anonymity_metrics.computeE2ELatency(packetLogs)

    print("\n\n")
    print("-------------------------------------------------------")
    print("Simulation finished. Below, you can check your results.")
    print("-------------------------------------------------------")
    print("-------- Anonymity metrics --------")
    print(">>> Entropy: ", entropy)
    if unlinkability[0] == None:
        print(">>> E2E Unlinkability: epsilon= -, delta=%f)" % unlinkability[1])
    else:
        print(">>> E2E Unlinkability: (epsilon=%f, delta=%f)" % unlinkability)
    print("\n\n")
    print("-------- Performance metrics --------")
    print(">> Overall latency: {:.3f} [ms]".format(latency*1000))
    print(">> Throughput of the network: {:.3f} [packets/s]".format(pps))
    print(">> Throughput of the network: {:.3f} [kB/s]".format(throughput / 1000))
    print("-------------------------------------------------------")

# except Exception as e:
# print(e)
# print("Something went wrong! Check whether your input parameters are correct.")
