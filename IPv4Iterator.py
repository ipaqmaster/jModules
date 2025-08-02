#!/usr/bin/env python
import ipaddress
import random

def feistel(i, size, seed, rounds):
    """
    Feistel cipher for 'randomly' shuffling the IPs of a IPv4Network range 
    based on the starting IP and total size without duplicates and with a definite end.
    """
    l = i >> 8
    r = i & 0xFF
    for _ in range(rounds):
        new_l = r
        new_r = l ^ ((r * seed) & 0xFF)
        l, r = new_l, new_r
    return ((l << 8) | r) % size

def ipRangeRandomOrder(start, size, seed):
    """
    The main function per IPv4Network object which iterates over IPs of a given network
    'randomly' referencing a seed and feistel function to make the magic happen.
    """
    #range(2**32) # All IPv4 space
    for i in range(size):
        ip = ipaddress.IPv4Address(start + feistel(i, size, seed, rounds=4))
        yield str(ip)

class IPv4Iterator:
    def __init__(self, target='0.0.0.0/0', excludes=['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'], seed=None, debug=False):
        self.target      = target
        self.excludes    = excludes

        if seed:
            random.seed(seed)
        self.feistelSeed = random.getrandbits(32)

        self.getTargets()
        self.makeGenerators()

    def getTargets(self):
        """
        Take a target subnet and subtracts subnets we wish to exclude.
        Results in multiple IPv4Network objects covering the ranges we want to scan.
        """

        overallTarget = ipaddress.IPv4Network(self.target)

        if not self.excludes:
            print('Targeting entire range: %s' % self.target)
            targets = [overallTarget]
        else:
            # Iterate over ranges we don't want to include in generation.
            excludes = [ipaddress.IPv4Network(s) for s in (self.excludes or [])]

            targets = [overallTarget]
            for exclude in excludes:
                newNetworks = []
                for network in targets:
                    if exclude.overlaps(network):
                        newNetworks.extend(network.address_exclude(exclude))
                    else:
                        newNetworks.append(network)
                targets = newNetworks

            print("Found %s subnets of %s after excluding ranges: %s" % (len(targets), self.target, self.excludes))

        self.targets = targets

    def makeGenerators(self):
        """
        Take all our network ranges post filtering for excluded ranges and make generator threads out of them.
        These will be used by the generate() function below at random until all generators return empty.
        """
        self.generators = []
        for target in self.targets:
            gen = ipRangeRandomOrder(start=int(target.network_address), size=int(target.num_addresses), seed=self.feistelSeed)
            next(gen) # Skip the first entry which happens to be the subnet itself. (TBD why)
            self.generators.append(gen)

    def generate(self):
        """
        From our generator functions (one defined for each network range)
        Pick one at random and have it yield something in its ranges.
        Runs near 594k IPs per second. But the bottleneck will be scanning.
        Guess my cpu's single core clock speed.
        """
        while True:
            if not self.generators:
                return

            generator = random.choice(self.generators)
            try:
                yield next(generator)
            except StopIteration:
                self.generators.remove(generator)

if __name__ == '__main__':
    print('Running with defaults...Outputting all public IPv4 space in a random order.')
    ipv4iterator = IPv4Iterator()
    for ip in ipv4iterator.generate():
        print(ip)
