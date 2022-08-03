import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.mem = {"last_attack": "D", "deaths": [], "priority_repair": [], "useful": []}

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        #game_state.attempt_spawn(DEMOLISHER, [24, 10], 3)
        gamelib.debug_write('Turn {}'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.
        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        gamelib.debug_write(self.mem)
        # builing-related stuff
        if game_state.turn_number < 5:
            gamelib.debug_write("building up initial defences")
            self.build_defences(game_state)
        else:
            self.priority_repair(game_state)
            if game_state.turn_number % 2 == 0:
                self.build_defences(game_state)

        #if game_state.turn_number > 8:
        #    if game_state.turn_number % 2 == 0:
        #        self.remove_useless(game_state)
        # Now build reactive defenses based on where the enemy scored
        self.build_reactive_defense(game_state)
        # First, place basic defenses
        
        # attacking-related stuff
        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        if game_state.turn_number < 5:
            #self.stall_with_interceptors(game_state)
            pass
        else:
            # Now let's analyze the enemy base to see where their defenses are concentrated.
            # If they have many units in the front we can build a line for our demolishers to attack them at long range.
            #if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
                #self.demolisher_line_strategy(game_state)
            
                # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

                # Only spawn Scouts every other turn
                # Sending more at once is better since attacks can only hit a single scout at a time

            if game_state.get_resources()[1] > 25:

                game_state.attempt_spawn(DEMOLISHER, [22, 8], 3)
                scout_spawn_location_options = [[13, 0], [14, 0], [15, 1]]
                best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                game_state.attempt_spawn(SCOUT, best_location, 1000)
            
            pass

            if game_state.number_affordable(SCOUT) > 15 and self.mem["last_attack"] == "D":
                    # To simplify we will just check sending them from back left and right
                scout_spawn_location_options = [[13, 0], [14, 0], [15, 1]]
                best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                game_state.attempt_spawn(SCOUT, best_location, 1000)
                self.mem["last_attack"] == "S"

            elif game_state.number_affordable(DEMOLISHER) > 5 and self.mem["last_attack"] == "S":
                game_state.attempt_spawn(DEMOLISHER, [15, 1], 5)
                self.mem["last_attack"] == "D"
                # Lastly, if we have spare SP, let's build some supports
                #support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
                #game_state.attempt_spawn(SUPPORT, support_locations)

    def priority_repair(self, game_state):

        gamelib.debug_write("priority repair of following destroyed units: ")
        gamelib.debug_write(self.mem["priority_repair"])
        
        # replace destroyed units
        for unit in self.mem["priority_repair"]:
            if game_state.can_spawn(unit[1], unit[0]): 
                game_state.attempt_spawn(unit[1], unit[0])
                self.mem["priority_repair"].remove(unit)
            if unit[1] == WALL:
                game_state.attempt_upgrade(unit[0])

    def remove_useless(self, game_state):

        for i in range(0, 14):
            for j in range(i, 27 - i):
                if game_state.contains_stationary_unit([j, i]) == TURRET and [j, i] not in self.mem["useful"]:
                    game_state.attempt_remove([j, i])

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[1, 12], [3, 12], [6, 12], [8, 12], [11, 12], [16, 12], [19, 12],
                            [22, 12], [23, 12], [24, 12], [26, 12], [12, 11], [15, 11], [12, 10], [15, 10]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)
        
        # Place walls in front of turrets to soak up damage for them
        wall_locations = [[0, 13], [1, 13], [2, 13], [3, 13], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13],
                          [9, 13], [10, 13], [11, 13], [12, 13], [15, 13], [16, 13], [17, 13], [18, 13],
                          [19, 13], [20, 13], [21, 13], [22, 13], [23, 13], [24, 13], [26, 13], [27, 13],
                          [12, 12], [15, 12], [23, 11], [22, 10], [21, 9], [20, 8], [19, 7], [18, 6], [17, 5], [16, 4]]

        support_locations = [[14, 4], [15, 4], [13, 3], [14, 3], [15, 3], [12, 2], [13, 2], [14, 2], [12, 1], [13, 1]]

        game_state.attempt_spawn(WALL, wall_locations)
        game_state.attempt_spawn(SUPPORT, support_locations)
        # upgrade walls so they soak more damage
        if game_state.get_resources()[0] > 5:
            gamelib.debug_write("wall upgrades")
            game_state.attempt_upgrade(wall_locations)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """

        no_zone = [[25, 13], [25, 12], [24, 11], [25, 11], [23, 10], [24, 10], [22, 9], [23, 9], [21, 8],
                   [22, 8], [20, 7], [21, 7], [19, 6], [20, 6], [18, 5], [19, 5], [17, 4], [18, 4], [16, 3],
                   [17, 3], [15, 2], [16, 2], [14, 1], [15, 1], [13, 0], [14, 0]]
        for location in self.scored_on_locations:
            bls = [[location[0], location[1]+2], [location[0]+2, location[1]], [location[0]-2, location[1]]]
            for build_location in bls:
                if build_location not in no_zone:
                    game_state.attempt_spawn(TURRET, build_location)

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        #stationary_units = [WALL, TURRET, SUPPORT]
        #cheapest_unit = WALL
        #for unit in stationary_units:
        #    unit_class = gamelib.GameUnit(unit, game_state.config)
        #    if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
        #        cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(19, 9, -1):
            game_state.attempt_spawn(WALL, [x, 5])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [18, 4], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]

        #for death in events["death"]:
        #    if death[3] == 1:
        #        self.mem["deaths"].append(death)
        gamelib.debug_write(events["death"])
        for death in events["death"]:
            if (death[1] in [0, 2]) and death[3] == 1 and not death[4]:
                gamelib.debug_write("added to priority repair")
                self.mem["priority_repair"].append([death[0], WALL if death[1] == 0 else TURRET])

        for attack in events["attack"]:
            if attack[3] == 2 and attack[6] == 1:
                self.mem["useful"].append([attack[0], TURRET, 0])

        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                #gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                #gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
