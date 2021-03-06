import logging

from assemblyline.common.attack_map import attack_map, software_map

heur_logger = logging.getLogger("assemblyline.heuristics")


def service_heuristic_to_result_heuristic(srv_heuristic, heuristics):
    heur_id = srv_heuristic['heur_id']
    attack_ids = srv_heuristic.pop('attack_ids', [])
    signatures = srv_heuristic.pop('signatures', {})
    frequency = srv_heuristic.pop('frequency', 0)
    score_map = srv_heuristic.pop('score_map', {})

    # Validate the heuristic and recalculate its score
    heuristic = Heuristic(heur_id, attack_ids, signatures, score_map, frequency, heuristics)

    try:
        # Assign the newly computed heuristic to the section
        output = dict(
            heur_id=heur_id,
            score=heuristic.score,
            name=heuristic.name,
            attack=[],
            signature=[]
        )

        # Assign the multiple attack IDs to the heuristic
        for attack_id in heuristic.attack_ids:
            attack_item = dict(
                attack_id=attack_id,
                pattern=attack_map[attack_id]['name'],
                categories=attack_map[attack_id]['categories']
            )
            output['attack'].append(attack_item)

        # Assign the multiple signatures to the heuristic
        for sig_name, freq in heuristic.signatures.items():
            signature_item = dict(
                name=sig_name,
                frequency=freq
            )
            output['signature'].append(signature_item)

        return output
    except InvalidHeuristicException as e:
        heur_logger.warning(str(e))
        raise


class InvalidHeuristicException(Exception):
    pass


class Heuristic(object):
    def __init__(self, heur_id, attack_ids, signatures, score_map, frequency, heuristics):
        # Validate heuristic
        definition = heuristics.get(heur_id)
        if not definition:
            raise InvalidHeuristicException(f"Heuristic with ID '{heur_id}' does not exist, skipping...")

        # Set defaults
        self.heur_id = heur_id
        self.attack_ids = []
        self.name = definition.name
        self.classification = definition.classification

        # Show only attack_ids that are valid
        attack_ids = attack_ids or []
        for a_id in attack_ids:
            if a_id in attack_map:
                self.attack_ids.append(a_id)
            elif a_id in software_map:
                for s_a_id in software_map[a_id]['attack_ids']:
                    if s_a_id in attack_map:
                        self.attack_ids.append(s_a_id)
                    else:
                        heur_logger.warning(f"Invalid related attack_id '{s_a_id}' for software '{a_id}' "
                                            f"in heuristic '{heur_id}'. Ignoring it.")
            else:
                heur_logger.warning(f"Invalid attack_id '{a_id}' in heuristic '{heur_id}'. Ignoring it.")
        self.attack_ids = list(set(self.attack_ids))

        # Calculate the score for the signatures
        self.signatures = signatures or {}
        if len(self.signatures) > 0:
            self.score = 0
            for sig_name, freq in signatures.items():
                sig_score = definition.signature_score_map.get(sig_name, score_map.get(sig_name, definition.score))
                self.score += sig_score * freq
        else:
            # Calculate the score for the heuristic frequency
            frequency = frequency or 1
            self.score = definition.score * frequency

        # Check scoring boundaries
        if definition.max_score:
            self.score = min(self.score, definition.max_score)
