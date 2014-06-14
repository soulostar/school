import math
import random
import simpy
import sys

if (len(sys.argv) != 3) or (sys.argv[2] != 'exponential' and sys.argv[2] != 'linear'):
	print "Error with arguments. Format is \n$ python simulation2.py lambda algorithm\n, where lambda is the packet arrival rate(float) and algorithm is either 'exponential' or 'linear'"
	exit(1) 

timeslot_size = 1
lambd = float(sys.argv[1])
backoff_algorithm = sys.argv[2]
packet_count = 5000
packets_in_node = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
next_transmit_timeslot = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
num_times_retransmitted = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
packets_remaining = packet_count * 10
seed = 5 # fixed seed for reproducibility of results

random.seed(seed)

def packet(env, arrive_time, node_number):
	yield env.timeout(arrive_time)
	packets_in_node[node_number] += 1
	if (packets_in_node[node_number] == 1):
		next_transmit_timeslot[node_number] = math.ceil(arrive_time)
		#print "Packet arrived at node %d. Will attempt transmit at %d, %d packets left to transmit" % (node_number, next_transmit_timeslot[node_number], packets_remaining)
	#else:
		#print "Packet arrived at node %d. %d packets in node." % (node_number, packets_in_node[node_number])
	
def timeslots(env):
	global packets_remaining
	successful_transmits = 0
	while True:		
		#print "Time slot %d:\n" % (env.now/timeslot_size)
		if next_transmit_timeslot.count(env.now) == 1:
			transmitting_node = next_transmit_timeslot.index(env.now)
			#print "---A successful transmit by node %d occurs.---" % transmitting_node
			packets_in_node[transmitting_node] -= 1
			if packets_in_node[transmitting_node] == 0:
				next_transmit_timeslot[transmitting_node] = -1
			else:
				#print "-----Node %d still has packet(s), next transmit attempt at time %d-----" % (transmitting_node, env.now + 1)
				next_transmit_timeslot[transmitting_node] = env.now + 1
			num_times_retransmitted[transmitting_node] = 0 
			packets_remaining -= 1
			successful_transmits += 1

		elif next_transmit_timeslot.count(env.now) > 1:
			#print "---A collision has occurred.---"
			for i in range(len(next_transmit_timeslot)):
				if (next_transmit_timeslot[i] == env.now):
					num_times_retransmitted[i] += 1 
					if backoff_algorithm == 'exponential':
						k = min(num_times_retransmitted[i], 10)
						next_transmit_timeslot[i] = env.now + math.ceil(random.uniform(0, 2**k))
					elif backoff_algorithm == 'linear':
						k = min(num_times_retransmitted[i], 1024)
						next_transmit_timeslot[i] = env.now + math.ceil(random.uniform(0, k))
					#print "-----Node %d collided, rescheduled for time %d-----" % (i, next_transmit_timeslot[i])					
		
		if packets_remaining == 0:
			print "%d/%d(%2.5f) transmit timeslots successful." % (successful_transmits, env.now+1, float(successful_transmits)/(env.now+1))
			break			
		yield env.timeout(timeslot_size)
	 
env = simpy.Environment()

env.process(timeslots(env))

for node_num in range(10):
	totalTime = 0
	for i in range(packet_count):
		interval = random.expovariate(lambd)
		totalTime += interval
		env.process(packet(env, totalTime, node_num))

env.run()

""" RESULTS:
					Throughput
					exponential			linear
--------------------------------------------------
	lambda=0.01		0.09770				0.09770				
	lambda=0.02		0.19540				0.19540
	lambda=0.03		0.29310				0.29310
	lambda=0.04		0.39080				0.29819
	lambda=0.05		0.48850				0.30181
	lambda=0.06		0.58340				0.29873
	lambda=0.07 	0.67374				0.30396
	lambda=0.08 	0.75322				0.29827
	lambda=0.09 	0.79933				0.30114
"""
	
	
