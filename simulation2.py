import math
import random
import simpy
import argparse

# Parse arguments
parser = argparse.ArgumentParser(description = "Simulate the throughput of Ethernet with different backoff algorithms.")
parser.add_argument('rate', metavar='lambda', type=float, help="packet arrival rate")
parser.add_argument('algorithm', metavar='algorithm', choices=['exponential', 'linear'], help="type of backoff algorithm to use ('exponential' or 'linear')")
parser.add_argument('-l','--log', action='store_true', default=False, help="flag to write to a log file")
parser.add_argument('-n', metavar='num_nodes', type=int, default=10, help='number of nodes')
parser.add_argument('-p', metavar='packet_count', type=int, default=5000, help='total packets to be transmitted per node')
parser.add_argument('-random', nargs='?', type=int, default=5, const=random.randrange(1,10000), help='random seed (fixed to 5 if -random is not present, set to a random integer from 1 to 10000 if -random is present but is not followed by an argument)')  
args = parser.parse_args()

# Packet arrival rate
lambd = args.rate

# Backoff algorithm to use: "exponential" or "linear"
backoff_algorithm = args.algorithm

# Logging flag
log = args.log
if log:
	output = open('log.txt', 'wb')

# Number of nodes
node_count = args.n

# Number of packets for each node to transmit
packet_count = args.p

# The number of packets currently in each node
packets_in_node = [0] * node_count

# The next transmit timeslot for each node
next_transmit_timeslot = [-1] * node_count

# The number of times each node has consecutively attempted to retransmit its current packet
num_times_retransmitted = [0] * node_count

# Default: fixed random seed for reproducibility of results
random.seed(args.random)

def log(message):
	""" Writes message to log.txt if log flag is enabled """
	if log:
		output.write(message)
		
def packet(env, arrive_time, node_number):
	""" Simulate the arrival of packets at nodes """
	yield env.timeout(arrive_time)
	packets_in_node[node_number] += 1
	# If node was previously empty, set a timeslot for next transmission
	if (packets_in_node[node_number] == 1):
		next_transmit_timeslot[node_number] = math.ceil(arrive_time)
		log("---Packet arrived at node %d. Will attempt transmit at t = %d, %d packet(s) in node---\n" % (node_number, next_transmit_timeslot[node_number], packets_in_node[node_number]))
	else:
		log("---Packet arrived at node %d. %d packet(s) in node.---\n" % (node_number, packets_in_node[node_number]))
	
def timeslots(env):
	""" Simulate the transmission of packets from nodes """
	packets_transmitted = 0
	while True:	
		log("Time slot %d:\n" % (env.now))

		# If only one node is attempting to transmit at current time, transmission is successful
		if next_transmit_timeslot.count(env.now) == 1:
			transmitting_node = next_transmit_timeslot.index(env.now)
			packets_in_node[transmitting_node] -= 1
			log("---Node %d successfully transmits. %d packet(s) remaining---\n" % (transmitting_node, packets_in_node[transmitting_node]))
			if packets_in_node[transmitting_node] == 0:
				next_transmit_timeslot[transmitting_node] = -1
			else:
				log("-----Node %d still has packet(s), next transmit attempt at time %d-----\n" % (transmitting_node, env.now + 1))
				next_transmit_timeslot[transmitting_node] = env.now + 1
			num_times_retransmitted[transmitting_node] = 0 
			packets_transmitted += 1

		# Transmission failure due to collision, retransmission times for each node involved randomized based on backoff algorithm
		elif next_transmit_timeslot.count(env.now) > 1:
			for i in range(len(next_transmit_timeslot)):
				if (next_transmit_timeslot[i] == env.now):
					log("---Node %d attempting transmit---\n" % i)
					num_times_retransmitted[i] += 1 
					if backoff_algorithm == 'exponential':
						k = min(num_times_retransmitted[i], 10)
						next_transmit_timeslot[i] = env.now + math.ceil(random.uniform(0, 2**k))
					elif backoff_algorithm == 'linear':
						k = min(num_times_retransmitted[i], 1024)
						next_transmit_timeslot[i] = env.now + math.ceil(random.uniform(0, k))
					log("-----Node %d collided, rescheduled for t = %d-----\n" % (i, next_transmit_timeslot[i]))					
		
		# All packets transmitted; print results
		if packets_transmitted == packet_count*node_count:
			print "%d/%d(%2.5f) transmit timeslots successful." % (packets_transmitted, env.now+1, float(packets_transmitted)/(env.now+1))
			log("\n%d/%d(%2.5f) transmit timeslots successful." % (packets_transmitted, env.now+1, float(packets_transmitted)/(env.now+1)))
			break			
		yield env.timeout(1)
	 
env = simpy.Environment()

env.process(timeslots(env))

for node_num in range(node_count):
	total_time = 0
	for i in range(packet_count):
		interval = random.expovariate(lambd)
		total_time += interval
		env.process(packet(env, total_time, node_num))

env.run()

""" RESULTS (nodes=10, packets=5000, seed=5):
			Throughput
			exponential			linear
--------------------------------------------------
	lambda=0.01	0.09770				0.09770				
	lambda=0.02	0.19540				0.19540
	lambda=0.03	0.29310				0.29310
	lambda=0.04	0.39080				0.29819
	lambda=0.05	0.48850				0.30181
	lambda=0.06	0.58340				0.29873
	lambda=0.07 	0.67374				0.30396
	lambda=0.08 	0.75322				0.29827
	lambda=0.09 	0.79933				0.30114
"""
	
	
