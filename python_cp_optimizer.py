import sys
from collections import namedtuple
from collections import defaultdict
from ortools.constraint_solver import pywrapcp

Player = namedtuple('Player', ['name', 'cost', 'position', 'value', 'team'], verbose=False)

def full_group_by(l, key):
    d = defaultdict(list)
    for item in l:
        d[key(item)].append(item)
    return d

    """Returns a list of lineups that meet given constraints
    
    Args:
        players: list of players (Player tuple)
        totalplayers: number of players in each lineup
        totalcost: cost constraint
        threshold: points constraint
        groups: groups requirements list, eg. [3,3,2]
        positions: positions requirements
        maxteamplayers: max number of players to choose from each team
        totalsolutions: max number of lineups to return
        locked: list of locked players
    """
def lineup_solver (players, totalplayers, totalcost, threshold, groups, positions,
        maxteamplayers, totalsolutions=100000, locked=[]):
    solver = pywrapcp.Solver("lineup optimizer")

    playervars = {i: solver.IntVar(0, 1, "player %i" % k) for k,i in enumerate(players)}
    teamgroups=full_group_by(players, lambda x: x.team)
    posgroups=full_group_by(players, lambda x: x.position)
    teamvars ={i:[solver.IntVar(0, 1, "%s %i" % (i,k)) for k in range(len(groups))] for i in teamgroups}

    # total players constraint
    #solver.Add(solver.Sum([playervars[i] for i in players]) == totalplayers)
    solver.Add(solver.Count([playervars[i] for i in players], 1, totalplayers))

    # total cost constraint
    solver.Add(solver.Sum([playervars[i]*int(i.cost) for i in players]) <= totalcost)

    # points threshold
    solver.Add(solver.Sum([playervars[i]*int(i.value) for i in players]) >= threshold)

    #positions constraint
    [solver.Add (solver.Sum([playervars[p] for p in posgroups.get(pos,[])]) >= positions.get(pos,0)) for pos in positions]

    # group constraints
    [solver.Add (solver.Sum([v[i] for k,v in teamvars.iteritems()]) == 1) for i in range(len(groups))]
    [solver.Add (solver.Sum([playervars[p] for p in teamgroups[i]]) >= solver.Sum([v*groups[n] for n,v in enumerate(teamvars[i])])) for i in teamgroups]

    # max players from one team
    [solver.Add (solver.Sum([playervars[p] for p in teamgroups[i]]) <= maxteamplayers) for i in teamgroups]

    # locked players
    [solver.Add (playervars[p] == 1) for p in locked]

    db = solver.Phase([playervars[i] for i in players]+[v for k in teamgroups for v in teamvars[k]],
                      solver.CHOOSE_MIN_SIZE_LOWEST_MAX,
                      solver.ASSIGN_CENTER_VALUE)

    solver.NewSearch(db)

    # Iterates through the solutions
    num_solutions = 0
    lineups=[]
    while solver.NextSolution() and num_solutions<totalsolutions:
      lineup = [i for i in players if int(playervars[i].Value())==1]
      lineups.append(lineup)
      #print lineup#, [[int(k.Value()) for k in teamvars[i]] for i in teamgroups] 
      num_solutions += 1
      if (num_solutions % 100) == 0:
        print num_solutions, "lineups found"
 
    solver.EndSearch()

    print
    print "Solutions found:", num_solutions
    print "Time:", solver.WallTime(), "ms"

    return lineups

def main():
    players=[]
    players.append(Player("plA1", 9000, "1B", 40.99, "tA"))
    players.append(Player("plA2", 8400, "1B", 43.56, "tA"))
    players.append(Player("plA3", 6700, "3B", 35.08, "tA"))
    players.append(Player("plA4", 2000, "OF", 31.57, "tA"))
    players.append(Player("plA5", 3000, "OF", 32.57, "tA"))
    players.append(Player("plA6", 4000, "C", 33.57, "tA"))
    players.append(Player("plA7", 5000, "OF", 34.57, "tA"))
    players.append(Player("plB1", 6000, "OF", 35.57, "tB"))
    players.append(Player("plB2", 1000, "1B", 40.99, "tB"))
    players.append(Player("plB3", 22400, "1B", 43.56, "tB"))
    players.append(Player("plB4", 2700, "3B", 33.08, "tB"))
    players.append(Player("plB5", 3000, "2B", 32.57, "tB"))
    players.append(Player("plB6", 4000, "OF", 38.57, "tB"))
    totalplayers=8
    totalcost=30000
    threshold=40
    groups=[3,3,2]
    positions={'1B':1, '2B':1, '3B':1, 'OF':3, 'SS':1, 'C':1}
    maxteamplayers = 5
    
    #lineup_solver(players, totalplayers, totalcost, threshold, groups, positions, maxteamplayers, [l])

    #optimize without locked player
    lineups=lineup_solver(players, totalplayers, totalcost, threshold, groups, positions, maxteamplayers)
if __name__=="__main__":
    main()
