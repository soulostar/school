import simpy
import random
import sys

# USAGE: $ python simulation1.py lambda B
# 	lambda = packet arrival rate, float
#	B = buffer capacity, integer

packetsInBuffer = 0
MEAN_ARRIVAL_TIME = 0.99
droppedPackets = 0
seed = 5 # fixed seed for reproducible results

def packet(env, name, buf, arrive_time, process_time, BUFFER_CAPACITY):
	global droppedPackets
	global packetsInBuffer
	yield env.timeout(arrive_time)

	#print "%s arrived at %f with %d packets in buffer" % (name, env.now, packetsInBuffer)
	if packetsInBuffer >= BUFFER_CAPACITY:
		#print "%s DROPPED" % name
		droppedPackets += 1
	else:
		packetsInBuffer += 1
		with buf.request() as req:
			yield req
			yield env.timeout(process_time)
			#print "%s out at %f, %d packets remain" % (name, env.now, packetsInBuffer-1)
		packetsInBuffer -= 1

def formula(lambd, mu, B):
	numerator = 1 - float(lambd)/mu
	denominator = 1 - (float(lambd)/mu)**(B+2)
	coefficient = (float(lambd)/mu)**(B+1)
	return coefficient * numerator / denominator

if (len(sys.argv) == 1):
	print "Error: no arguments provided. USAGE: $ python simulation1.py lambda B, where lambda is the packet arrival rate(float) and B is the buffer capacity(int)"
	exit(1)
elif (len(sys.argv) == 2):
	print "Incomplete argument list. Two arguments required: packet arrival rate (float) and buffer capacity (int)."
	exit(1)
elif (len(sys.argv) > 3):
	print "Too many arguments. Two arguments required: packet arrival rate (float) and buffer capacity (int)."
	exit(1)

env = simpy.Environment()
buf = simpy.Resource(env, capacity=1)
random.seed(seed)

def simulate(lambd, b, packetCount):
	totalTime = 0
	for i in range(packetCount):
		interval = random.expovariate(lambd)
		totalTime += interval
		process_time = random.expovariate(1)
		#print "packet %d times generated: arrive at %f, %f to process" % (i+1, totalTime, process_time)
		env.process(packet(env, 'Packet %d' % (i+1), buf, totalTime, process_time, b))

	env.run()
	print "lambda = %1.2f, mu = %1.2f, B = %d" % (lambd, 1, b) 
	print "%d/%d(%2.5f percent) packets dropped in simulation" % (droppedPackets, packetCount, (float(droppedPackets)/packetCount) * 100)

	print "%2.5f percent packets dropped by formula\n" % (formula(lambd, 1, b) * 100)

simulate(float(sys.argv[1]), int(sys.argv[2]), 50000)

""" RESULTS:
----------------------------------------------------------------|
				Packet drop percentage(simulated, calculated)   |
				B=10				B=50					    |
----------------------------------------------------------------|
	lambda=0.2	0.00000/0.00000		0.00000/0.00000			    |
	lambda=0.4	0.00400/0.00252		0.00000/0.00000				|
	lambda=0.6	0.29000/0.14544		0.00000/0.00000				|
	lambda=0.8	2.25600/1.84476		0.00000/0.00023				|
	lambda=0.9	4.78800/4.37324		0.07200/0.04658				|
	lambda=0.99	8.24400/7.88045		1.35400/1.47152				|
----------------------------------------------------------------|
"""

