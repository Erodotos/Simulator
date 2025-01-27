import math
import random
import numpy
from classes.Node import Node
from classes.Client import Client
import experiments.Settings
import os


class Network(object):

    def __init__(self, env, type, imbalanced, conf, loggers):
        self.env = env
        self.conf = conf
        self.topology = {}
        self.type = type
        self.loggers = loggers

        self.clients = [Client(env, conf, self, loggers = loggers, label=0) for i in range(int(conf["clients"]["number"]))]

        if type == "p2p":
            self.peers = [Node(env, conf, self, id="Peer%s" % i, loggers = loggers) for i in range(int(conf["clients"]["number"]))]
            self.topology["Type"] = "p2p"
            self.init_p2p()
        else:
            if type == "cascade":
                self.topology["Type"] = "cascade"
                self.mixnodes = [Node(env, conf, self, id="M%s" % i, loggers = loggers) for i in range(self.conf["network"]["cascade"]["cascade_len"])]
                self.init_cascade()
            elif type == "stratified":
                self.topology["Type"] = "stratified"
                self.topology["imbalanced"] = imbalanced
                # num_mixnodes = int(self.conf["network"]["stratified"]["layers"]) * int(self.conf["network"]["stratified"]["layer_size"])
                num_mixnodes = 25
                self.mixnodes = [Node(env, conf, self, id="M%s" % i, loggers = loggers) for i in range(num_mixnodes)]
                # self.init_stratified()
                self.init_stratified_imbalanced_2_1_2()
            elif type == "multi_cascade":
                self.topology["Type"] = "multi_cascade"
                num_mixnodes = int(self.conf["network"]["multi_cascade"]["cascade_len"]) * int(self.conf["network"]["multi_cascade"]["num_cascades"])
                self.mixnodes = [Node(env, conf, self, id="M%s" % i, loggers = loggers) for i in range(num_mixnodes)]
                self.init_multi_cascade()
            else:
                raise Exception("Didn't recognize the network type")
        print("Current topology: ", self.topology["Type"])
        # print("Batching yes/no: ", self.conf["mixnodes"]["batch"])

    def init_p2p(self):
        self.topology["peers"] = self.peers.copy()

    def init_cascade(self):
        self.topology["cascade"] = self.mixnodes.copy()

    def init_multi_cascade(self):
        num_cascades = int(self.conf["network"]["multi_cascade"]["num_cascades"])
        cascade_len = int(self.conf["network"]["multi_cascade"]["cascade_len"])
        ind_cascades = [self.mixnodes[x:x+cascade_len] for x in range(0, len(self.mixnodes), cascade_len)]
        self.topology["cascades"] = ind_cascades

    def init_stratified(self):
        num_layers = int(self.conf["network"]["stratified"]["layers"])
        mixes_per_layer = int(self.conf["network"]["stratified"]["layer_size"])

        layers = [self.mixnodes[i * mixes_per_layer:(i + 1) * mixes_per_layer] for i in range(0, num_layers)]
        self.topology["Layers"] =  layers

        for i in range(0, num_layers - 1):
            for j in range(0, mixes_per_layer):
                self.topology[self.mixnodes[i * mixes_per_layer + j]] = layers[i + 1]

    def init_stratified_imbalanced_2_1_2(self):
        num_layers = int(self.conf["network"]["stratified"]["layers"])

        mixes_per_layer = [10,5,10]

        layers = []
        
        i = 0
        for ml in mixes_per_layer:
            tmp_layers = self.mixnodes[i:(i + ml)]
            layers.append(tmp_layers)
            i = i + ml
        self.topology["Layers"] =  layers

        
        for i in range (0,len(layers)-1):
            for mix in layers[i]:
                self.topology[mix] = layers[i + 1] 
  

    def select_random_route(self):
        tmp_route = []

        if self.topology["Type"] == "stratified":
            if self.topology["imbalanced"] == True:
                # First attempt
                # tmp_route = []
                # for L in self.topology["Layers"]:
                #     random_mix = None
                #     while True:
                #         random_mix = random.choice(L)
                #         rnd_prob = random.random()
                #         if rnd_prob < 0.5:
                #             continue
                #         else:
                #             tmp_route.append(random_mix)
                #             break
                # Second attempt
                
                layers_with_non_crashed_mixes = []
                for L in self.topology["Layers"]:
                    non_crashed_mixes = []
                    while True:
                        for mix in L:
                            if random.random() > 0.4:   # this is not actually random. this is pseudo random
                                non_crashed_mixes.append(mix)
                        if len(non_crashed_mixes) == 0:
                            print("zero-sequence")
                        else:
                            break

                    layers_with_non_crashed_mixes.append(non_crashed_mixes)
                tmp_route = [random.choice(L) for L in layers_with_non_crashed_mixes]
            else:
                tmp_route = [random.choice(L) for L in self.topology["Layers"]]
        elif self.topology["Type"] == "cascade":
            tmp_route = self.topology["cascade"].copy()
        elif self.topology["Type"] == "multi_cascade":
            tmp_route = random.choice(self.topology["cascades"])
        elif self.topology["Type"] == "p2p":
            length = self.conf["network"]["p2p"]["path_length"]
            tmp_route = random.sample(self.peers, length)
        

        return tmp_route


    def forward_packet(self, packet):
        ''' Function responsible for forwarding the packet, i.e.,
            checking what is the next hop of the packet and triggering the
            process_packet function by a particular node.

            Keyword arguments:
            packet - the packet to be forwarded.
        '''
        # TODO: If needed, some network delay can be added.
        yield self.env.timeout(0)

        # print(packet.current_node, packet.route, packet.dest)
        next_node = packet.route[packet.current_node + 1]
        packet.current_node += 1
        self.env.process(next_node.process_packet(packet))


    def __repr__(self):
        return "topology: " + str(self.topology)
