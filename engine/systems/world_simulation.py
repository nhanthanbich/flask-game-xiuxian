"""
World Simulation System - Sect Power, NPC Autonomy, Regional Control
Data-driven world state that evolves based on player actions
"""

import random
from typing import Dict, List, Tuple, Any
from enum import Enum
from datetime import datetime


class SectStatus(Enum):
    """Sect power thresholds"""
    DOMINANT = "Cường Thạc"  # 80+
    THRIVING = "Thịnh Thịnh"  # 60-79
    NORMAL = "Bình Thường"  # 40-59
    DECLINING = "Suy Vong"  # 20-39
    CRITICAL = "Cực Kỳ Suy"  # <20
    DISSOLVED = "Giải Thể"  # Extinct


class SectPowerEngine:
    """Manages sect power dynamics"""

    def __init__(self):
        # Sect status tracking
        self.sect_status = {}  # sect_id -> {power, members, reputation, treasury}
        self.sect_changes = {}  # Track quarterly changes
        self.regional_control = {}  # region -> {sect_id: percentage}
        self.sect_relationships = {}  # sect -> [rival_sects]

    def initialize_sects(self, sects_data: Dict):
        """Initialize sect status from game data"""
        for sect_id, sect_info in sects_data.items():
            self.sect_status[sect_id] = {
                'power': sect_info.get('power', 50),
                'power_change': 0,
                'members': sect_info.get('member_count', 20),
                'deaths_this_year': 0,
                'promotions_this_year': 0,
                'reputation': sect_info.get('reputation', 50),
                'treasury': sect_info.get('treasury', 1000),
                'wins': 0,
                'losses': 0,
                'region_control': sect_info.get('regions', ['Central']),
                'status': self._get_status(sect_info.get('power', 50))
            }

    def _get_status(self, power: int) -> str:
        """Determine sect status from power level"""
        if power >= 80:
            return SectStatus.DOMINANT.value
        elif power >= 60:
            return SectStatus.THRIVING.value
        elif power >= 40:
            return SectStatus.NORMAL.value
        elif power >= 20:
            return SectStatus.DECLINING.value
        elif power > 0:
            return SectStatus.CRITICAL.value
        else:
            return SectStatus.DISSOLVED.value

    def yearly_calculation(self, year: int):
        """Called yearly to update sect power"""
        for sect_id, status in self.sect_status.items():
            # Base calculation
            power_change = 0

            # Member promotions (+2 per promotion)
            promotions = status.get('promotions_this_year', 0)
            power_change += promotions * 2

            # Member deaths (-5 per death)
            deaths = status.get('deaths_this_year', 0)
            power_change -= deaths * 5

            # Wins vs rivals (+10 per win)
            wins = status.get('wins', 0)
            power_change += wins * 10

            # Losses vs rivals (-10 per loss)
            losses = status.get('losses', 0)
            power_change -= losses * 10

            # Random events (±5 to ±15)
            event_change = random.randint(-15, 15)
            if event_change != 0:
                power_change += event_change

            # Corruption/decline (-3 if no growth)
            if power_change < 0:
                power_change -= 3

            # Apply change
            status['power'] = max(0, status['power'] + power_change)
            status['power_change'] = power_change
            status['status'] = self._get_status(status['power'])

            # Reset yearly counters
            status['deaths_this_year'] = 0
            status['promotions_this_year'] = 0
            status['wins'] = 0
            status['losses'] = 0

    def record_member_event(self, sect_id: str, event_type: str, count: int = 1):
        """Record member promotions/deaths"""
        if sect_id not in self.sect_status:
            return

        if event_type == 'promotion':
            self.sect_status[sect_id]['promotions_this_year'] += count
            self.sect_status[sect_id]['members'] = max(0,
                self.sect_status[sect_id]['members'] + count)
        elif event_type == 'death':
            self.sect_status[sect_id]['deaths_this_year'] += count
            self.sect_status[sect_id]['members'] = max(0,
                self.sect_status[sect_id]['members'] - count)

    def record_conflict(self, sect_a: str, sect_b: str, winner: str, power_stake: int = 10):
        """Record sect conflict outcome"""
        if winner == sect_a:
            self.sect_status[sect_a]['wins'] = self.sect_status[sect_a].get('wins', 0) + 1
            self.sect_status[sect_b]['losses'] = self.sect_status[sect_b].get('losses', 0) + 1
        else:
            self.sect_status[sect_b]['wins'] = self.sect_status[sect_b].get('wins', 0) + 1
            self.sect_status[sect_a]['losses'] = self.sect_status[sect_a].get('losses', 0) + 1

    def get_sect_status(self, sect_id: str) -> Dict:
        """Get comprehensive sect status"""
        return self.sect_status.get(sect_id, {}).copy()

    def get_all_sect_rankings(self) -> List[Tuple[str, int, str]]:
        """Get sects ranked by power"""
        rankings = []
        for sect_id, status in self.sect_status.items():
            if status['power'] > 0:  # Only living sects
                rankings.append((sect_id, status['power'], status['status']))

        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings


class NPCAutonomy:
    """NPC autonomous behavior outside player interaction"""

    def __init__(self):
        self.npc_actions = {}  # npc_id -> {last_action, action_type, date}
        self.npc_lifecycle = {}  # npc_id -> {alive, sect_id, retirement_status}

    def initialize_npcs(self, npcs_data: Dict):
        """Initialize NPC life tracking"""
        for npc_id, npc_info in npcs_data.items():
            self.npc_lifecycle[npc_id] = {
                'alive': True,
                'sect_id': npc_info.get('sect_id'),
                'realm_level': npc_info.get('realm_index', 0),
                'retirement_status': None,
                'mission_cooldown': 0,
                'times_died': 0
            }

    def quarterly_npc_behavior(self, npc_id: str, sect_power: int, year: int, quarter: int) -> List[str]:
        """Process NPC behavior for a quarter"""
        if npc_id not in self.npc_lifecycle:
            return []

        npc = self.npc_lifecycle[npc_id]
        events = []

        if not npc['alive']:
            return events

        # Retire if high realm and time served
        if npc['realm_level'] >= 5 and random.random() < 0.15:  # 15% chance
            npc['retirement_status'] = f"Year {year}"
            events.append(f"🧘 {npc_id} tuyên bố rút khỏi giang hồ")
            return events

        # Leave if sect in crisis
        if sect_power < 30 and random.random() < 0.4:  # 40% chance
            npc['sect_id'] = None  # Free agent
            events.append(f"🚶 {npc_id} rời bỏ tông môn để tìm con đường mới")
            return events

        # Take mission from sect
        if random.random() < 0.6 and sect_power > 20:  # 60% chance if sect stable
            events.append(f"📜 {npc_id} nhận nhiệm vụ từ tông môn")

            # 30% chance of combat mission resulting in death
            if random.random() < 0.3:
                if random.random() < 0.15:  # 15% death rate
                    npc['alive'] = False
                    npc['times_died'] += 1
                    events.append(f"💀 {npc_id} hy sinh trong nhiệm vụ")
                else:
                    events.append(f"⚔️ {npc_id} chiến đấu nhưng sống sót")
            else:
                events.append(f"✅ {npc_id} hoàn thành nhiệm vụ thành công")

        # Learn new technique
        if random.random() < 0.2 and npc['realm_level'] >= 1:  # 20% chance
            events.append(f"📚 {npc_id} học được công pháp mới")
            # This would update NPC stats in game

        return events

    def get_npc_status(self, npc_id: str) -> Dict:
        """Get NPC current status"""
        return self.npc_lifecycle.get(npc_id, {}).copy()

    def get_living_npcs(self, sect_id: str = None) -> List[str]:
        """Get list of living NPCs, optionally by sect"""
        living = []
        for npc_id, status in self.npc_lifecycle.items():
            if status['alive']:
                if sect_id is None or status['sect_id'] == sect_id:
                    living.append(npc_id)
        return living


class RegionalControl:
    """Track sect control over world regions"""

    def __init__(self, regions: List[str]):
        self.regions = regions
        self.region_control = {}  # region -> {sect_id: control_percentage}
        self.conflicts_log = []  # Track historical conflicts

        # Initialize neutral
        for region in regions:
            self.region_control[region] = {}

    def set_region_control(self, region: str, sect_id: str, percentage: float):
        """Set sect control percentage in region (0-100)"""
        if region not in self.region_control:
            return

        self.region_control[region][sect_id] = max(0, min(100, percentage))

    def annual_regional_conflict(self, year: int, sect_status: Dict) -> List[str]:
        """Simulate annual regional conflicts"""
        events = []

        for region in self.regions:
            # Get sects in region
            sects_in_region = [(sect, pct)
                              for sect, pct in self.region_control[region].items()
                              if pct > 0]

            if len(sects_in_region) < 2:
                continue

            # Pick two strongest
            sects_in_region.sort(key=lambda x: x[1], reverse=True)
            sect_a, control_a = sects_in_region[0]
            sect_b, control_b = sects_in_region[1]

            # Conflict check
            if random.random() < 0.3:  # 30% chance of conflict
                power_a = sect_status.get(sect_a, {}).get('power', 50)
                power_b = sect_status.get(sect_b, {}).get('power', 50)

                # Weighted by power
                total = power_a + power_b
                winner_chance = power_a / total

                if random.random() < winner_chance:
                    winner = sect_a
                    loser = sect_b
                else:
                    winner = sect_b
                    loser = sect_a

                # Update control
                control_shift = 5  # percentage points
                self.region_control[region][winner] = min(100,
                    self.region_control[region].get(winner, 0) + control_shift)
                self.region_control[region][loser] = max(0,
                    self.region_control[region].get(loser, 0) - control_shift)

                events.append(
                    f"⚔️ Trong vùng {region}: {winner} chiến thắng {loser}, "
                    f"kiểm soát {self.region_control[region][winner]}%"
                )

        return events

    def get_region_control(self, region: str) -> Dict[str, float]:
        """Get current control percentages in region"""
        return self.region_control.get(region, {}).copy()


class CourtSystem:
    """Government/court system"""

    def __init__(self):
        self.power = 100  # Always strong
        self.official_sects = []
        self.suppressed_sects = []
        self.wanted_list = []  # NPC IDs wanted by court
        self.annual_taxes = {}  # sect -> tax amount

    def recognize_sect(self, sect_id: str):
        """Court officially recognizes a sect"""
        if sect_id not in self.official_sects:
            self.official_sects.append(sect_id)
        if sect_id in self.suppressed_sects:
            self.suppressed_sects.remove(sect_id)

    def suppress_sect(self, sect_id: str) -> str:
        """Court suppresses a sect"""
        if sect_id not in self.suppressed_sects:
            self.suppressed_sects.append(sect_id)
        if sect_id in self.official_sects:
            self.official_sects.remove(sect_id)

        return f"⚖️ Triều đình chính thức cấm tông môn {sect_id}"

    def add_to_wanted(self, npc_id: str):
        """Add NPC to wanted list"""
        if npc_id not in self.wanted_list:
            self.wanted_list.append(npc_id)

    def is_wanted(self, npc_id: str) -> bool:
        """Check if NPC is wanted"""
        return npc_id in self.wanted_list

    def set_tax(self, sect_id: str, amount: int):
        """Set annual tax for sect"""
        self.annual_taxes[sect_id] = amount


class WorldSimulation:
    """Main world simulation engine"""

    def __init__(self):
        self.sect_power = SectPowerEngine()
        self.npc_autonomy = NPCAutonomy()
        self.regions = RegionalControl([
            '清雲', '南蠻', '北荒', '中原', '西界'
        ])
        self.court = CourtSystem()
        self.world_events = []  # Chronicle of major events
        self.current_year = 1
        self.current_month = 1

    def initialize(self, game_state: Dict):
        """Initialize world from game data"""
        self.sect_power.initialize_sects(game_state.get('sects', {}))
        self.npc_autonomy.initialize_npcs(game_state.get('npcs', {}))

        # Set initial regional control
        for region, control in game_state.get('regional_control', {}).items():
            for sect, pct in control.items():
                self.regions.set_region_control(region, sect, pct)

    def advance_year(self) -> Dict[str, List[str]]:
        """Yearly world update"""
        events = {'major_events': [], 'sect_events': {}, 'npc_events': []}

        # Yearly sect power calculation
        self.sect_power.yearly_calculation(self.current_year)

        # Check for threshold changes
        for sect_id, status in self.sect_power.sect_status.items():
            old_status = status.get('status', '')
            new_status = self._get_status(status['power'])

            if old_status != new_status:
                events['major_events'].append(
                    f"🏛️ Year {self.current_year}: {sect_id} bây giờ "
                    f"ở tình trạng '{new_status}'"
                )

            events['sect_events'][sect_id] = [
                f"Power {status['power']} ({status['power_change']:+d})",
                f"Members: {status['members']}",
                f"Reputation: {status['reputation']}/100"
            ]

        # Regional conflicts
        conflict_events = self.regions.annual_regional_conflict(
            self.current_year,
            self.sect_power.sect_status
        )
        events['major_events'].extend(conflict_events)

        # NPC quarterly behavior
        for quarter in range(1, 5):
            for npc_id in self.npc_autonomy.npc_lifecycle:
                sect_id = self.npc_autonomy.npc_lifecycle[npc_id].get('sect_id')
                if sect_id and sect_id in self.sect_power.sect_status:
                    sect_power = self.sect_power.sect_status[sect_id]['power']
                    npc_events = self.npc_autonomy.quarterly_npc_behavior(
                        npc_id, sect_power, self.current_year, quarter
                    )
                    events['npc_events'].extend(npc_events)

        self.current_year += 1
        self.world_events.extend(events['major_events'])

        return events

    def player_action_impact(self, action_type: str, sect_id: str, amount: int = 10):
        """Record player impact on world"""
        if action_type == 'join_sect':
            self.sect_power.sect_status[sect_id]['members'] += 1
            self.sect_power.sect_status[sect_id]['power'] += 5

        elif action_type == 'quest_for_sect':
            self.sect_power.sect_status[sect_id]['power'] += amount

        elif action_type == 'defeat_npc':
            if sect_id in self.sect_power.sect_status:
                self.sect_power.record_member_event(sect_id, 'death', 1)
                self.sect_power.sect_status[sect_id]['power'] -= 20

    def save_state(self) -> Dict:
        """Save world state for persistence"""
        return {
            'sect_status': self.sect_power.sect_status,
            'npc_lifecycle': self.npc_autonomy.npc_lifecycle,
            'regional_control': self.regions.region_control,
            'court_official_sects': self.court.official_sects,
            'court_suppressed_sects': self.court.suppressed_sects,
            'court_wanted_list': self.court.wanted_list,
            'world_events': self.world_events,
            'current_year': self.current_year,
            'current_month': self.current_month
        }

    def load_state(self, state: Dict):
        """Load world state"""
        self.sect_power.sect_status = state.get('sect_status', {})
        self.npc_autonomy.npc_lifecycle = state.get('npc_lifecycle', {})
        self.regions.region_control = state.get('regional_control', {})
        self.court.official_sects = state.get('court_official_sects', [])
        self.court.suppressed_sects = state.get('court_suppressed_sects', [])
        self.court.wanted_list = state.get('court_wanted_list', [])
        self.world_events = state.get('world_events', [])
        self.current_year = state.get('current_year', 1)
        self.current_month = state.get('current_month', 1)

    def _get_status(self, power: int) -> str:
        """Helper for status calculation"""
        if power >= 80:
            return '强盛'
        elif power >= 60:
            return '兴盛'
        elif power >= 40:
            return '平稳'
        elif power >= 20:
            return '衰退'
        elif power > 0:
            return '危机'
        else:
            return '已解散'


# Global instance
world_simulation = WorldSimulation()
