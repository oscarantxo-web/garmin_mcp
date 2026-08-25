"""
High-level workout builders for Garmin Connect MCP Server.

These tools construct the internal Garmin Connect JSON internally and delegate
to the existing upload_workout / schedule_workout endpoints.
"""
import json
from typing import Any, Dict, List, Optional

# The garmin_client will be set by the main file
garmin_client = None


def configure(client):
    """Configure the module with the Garmin client instance"""
    global garmin_client
    garmin_client = client


# =============================================================================
# JSON BUILDERS
# =============================================================================

HR_ZONE_MAP = {
    "Z1": 1,
    "Z2": 2,
    "Z3": 3,
    "Z4": 4,
    "Z5": 5,
}


def _zone_number(zone: str) -> int:
    """Resolve a human-friendly zone string like 'Z3' to Garmin's zoneNumber."""
    zone_upper = zone.strip().upper()
    if zone_upper in HR_ZONE_MAP:
        return HR_ZONE_MAP[zone_upper]
    # Fallback: if user passed a digit directly
    try:
        z = int(zone_upper)
        if 1 <= z <= 5:
            return z
    except ValueError:
        pass
    raise ValueError(f"Invalid hr_zone '{zone}'. Use Z1-Z5 or 1-5.")


def build_run_json(
    name: str,
    run_seconds: int,
    warmup_min: int,
    cooldown_min: int,
    hr_zone: str = "Z3",
) -> dict:
    """Build the Garmin Connect JSON for a continuous run workout."""
    zone = _zone_number(hr_zone)
    run_display = (
        f"{run_seconds // 60}m" if run_seconds % 60 == 0 else f"{run_seconds}s"
    )
    return {
        "workoutName": name,
        "description": (
            f"{warmup_min}m warmup + {run_display} run Z{zone} + {cooldown_min}m cooldown"
        ),
        "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
        "workoutSegments": [{
            "segmentOrder": 1,
            "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
            "workoutSteps": [
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 1,
                    "stepType": {"stepTypeId": 1, "stepTypeKey": "warmup"},
                    "description": f"Warmup {warmup_min} min",
                    "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                    "endConditionValue": float(warmup_min * 60),
                    "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
                },
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 2,
                    "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
                    "description": f"Run {run_seconds}s Z{zone}",
                    "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                    "endConditionValue": float(run_seconds),
                    "targetType": {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"},
                    "zoneNumber": zone,
                },
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 3,
                    "stepType": {"stepTypeId": 2, "stepTypeKey": "cooldown"},
                    "description": f"Cooldown {cooldown_min} min",
                    "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                    "endConditionValue": float(cooldown_min * 60),
                    "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
                },
            ],
        }],
    }


def build_walk_run_json(
    name: str,
    run_seconds: int,
    walk_seconds: int,
    repeats: int,
    warmup_min: int,
    cooldown_min: int,
    hr_zone: str = "Z3",
) -> dict:
    """Build the Garmin Connect JSON for a walk/run interval workout.

    Parameters match create_walk_run_workout exactly.
    """
    zone = _zone_number(hr_zone)
    return {
        "workoutName": name,
        "description": (
            f"{warmup_min}m warmup + {repeats}x({run_seconds}s run / {walk_seconds}s walk) Z{zone} + "
            f"{cooldown_min}m cooldown"
        ),
        "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
        "workoutSegments": [{
            "segmentOrder": 1,
            "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
            "workoutSteps": [
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 1,
                    "stepType": {"stepTypeId": 1, "stepTypeKey": "warmup"},
                    "description": f"Warmup {warmup_min} min",
                    "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                    "endConditionValue": float(warmup_min * 60),
                    "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
                },
                {
                    "type": "RepeatGroupDTO",
                    "stepOrder": 2,
                    "numberOfIterations": repeats,
                    "workoutSteps": [
                        {
                            "type": "ExecutableStepDTO",
                            "stepOrder": 1,
                            "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
                            "description": f"Run {run_seconds}s Z{zone}",
                            "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                            "endConditionValue": float(run_seconds),
                            "targetType": {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"},
                            "zoneNumber": zone,
                        },
                        {
                            "type": "ExecutableStepDTO",
                            "stepOrder": 2,
                            "stepType": {"stepTypeId": 4, "stepTypeKey": "recovery"},
                            "description": f"Walk {walk_seconds}s Z{zone}",
                            "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                            "endConditionValue": float(walk_seconds),
                            "targetType": {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"},
                            "zoneNumber": zone,
                        },
                    ],
                },
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 3,
                    "stepType": {"stepTypeId": 2, "stepTypeKey": "cooldown"},
                    "description": f"Cooldown {cooldown_min} min",
                    "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                    "endConditionValue": float(cooldown_min * 60),
                    "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
                },
            ],
        }],
    }


def build_z2_walk_json(
    name: str,
    duration_min: int,
    hr_min: int,
    hr_max: int,
) -> dict:
    """Build the Garmin Connect JSON for a steady Z2 walking workout with absolute HR range."""
    return {
        "workoutName": name,
        "description": f"Walk {duration_min} min at Z2 ({hr_min}-{hr_max} bpm)",
        "sportType": {"sportTypeId": 12, "sportTypeKey": "walking"},
        "workoutSegments": [{
            "segmentOrder": 1,
            "sportType": {"sportTypeId": 12, "sportTypeKey": "walking"},
            "workoutSteps": [
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 1,
                    "stepType": {"stepTypeId": 1, "stepTypeKey": "warmup"},
                    "description": "Warmup 5 min",
                    "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                    "endConditionValue": 300.0,
                    "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
                },
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 2,
                    "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
                    "description": f"Walk {duration_min} min Z2",
                    "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                    "endConditionValue": float(duration_min * 60),
                    "targetType": {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"},
                    "zoneNumber": 2,
                },
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 3,
                    "stepType": {"stepTypeId": 2, "stepTypeKey": "cooldown"},
                    "description": "Cooldown 5 min",
                    "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                    "endConditionValue": 300.0,
                    "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
                },
            ],
        }],
    }


# =============================================================================
# CATÁLOGO Y RESOLUTOR DE EJERCICIOS DE FUERZA DE GARMIN CONNECT
# =============================================================================

EXERCISE_MAP = {
    # ── PECHO / CHEST ──
    "press banca": ("BENCH_PRESS", "BARBELL_BENCH_PRESS"),
    "press de banca": ("BENCH_PRESS", "BARBELL_BENCH_PRESS"),
    "press de banca con barra": ("BENCH_PRESS", "BARBELL_BENCH_PRESS"),
    "press banca barra": ("BENCH_PRESS", "BARBELL_BENCH_PRESS"),
    "barbell bench press": ("BENCH_PRESS", "BARBELL_BENCH_PRESS"),
    "bench press": ("BENCH_PRESS", "BARBELL_BENCH_PRESS"),
    "press pecho": ("BENCH_PRESS", "DUMBBELL_BENCH_PRESS"),
    "press de pecho": ("BENCH_PRESS", "DUMBBELL_BENCH_PRESS"),
    "press de banca con mancuernas": ("BENCH_PRESS", "DUMBBELL_BENCH_PRESS"),
    "press banca mancuernas": ("BENCH_PRESS", "DUMBBELL_BENCH_PRESS"),
    "press mancuerna": ("BENCH_PRESS", "DUMBBELL_BENCH_PRESS"),
    "press mancuernas": ("BENCH_PRESS", "DUMBBELL_BENCH_PRESS"),
    "dumbbell bench press": ("BENCH_PRESS", "DUMBBELL_BENCH_PRESS"),
    "press inclinado": ("BENCH_PRESS", "INCLINE_DUMBBELL_BENCH_PRESS"),
    "press inclinado barra": ("BENCH_PRESS", "INCLINE_BARBELL_BENCH_PRESS"),
    "press banca inclinado": ("BENCH_PRESS", "INCLINE_BARBELL_BENCH_PRESS"),
    "press inclinado mancuernas": ("BENCH_PRESS", "INCLINE_DUMBBELL_BENCH_PRESS"),
    "incline bench press": ("BENCH_PRESS", "INCLINE_DUMBBELL_BENCH_PRESS"),
    "press declinado": ("BENCH_PRESS", "DECLINE_BARBELL_BENCH_PRESS"),
    "flexiones": ("PUSH_UP", "PUSH_UP"),
    "flexion": ("PUSH_UP", "PUSH_UP"),
    "flexión": ("PUSH_UP", "PUSH_UP"),
    "push up": ("PUSH_UP", "PUSH_UP"),
    "pushup": ("PUSH_UP", "PUSH_UP"),
    "pushups": ("PUSH_UP", "PUSH_UP"),
    "flexiones diamante": ("PUSH_UP", "DIAMOND_PUSH_UP"),
    "aperturas": ("FLYE", "DUMBBELL_FLYE"),
    "aperturas mancuernas": ("FLYE", "DUMBBELL_FLYE"),
    "aperturas inclinadas": ("FLYE", "INCLINE_DUMBBELL_FLYE"),
    "cruces polea": ("FLYE", "CABLE_CROSSOVER"),
    "cruces en polea": ("FLYE", "CABLE_CROSSOVER"),
    "cable crossover": ("FLYE", "CABLE_CROSSOVER"),
    "fondos paralelas": ("DIP", "CHEST_DIP"),
    "fondos pecho": ("DIP", "CHEST_DIP"),
    "chest dip": ("DIP", "CHEST_DIP"),
    "pullover": ("PULLOVER", "DUMBBELL_PULLOVER"),

    # ── ESPALDA / BACK ──
    "remo con barra": ("ROW", "BARBELL_ROW"),
    "remo barra": ("ROW", "BARBELL_ROW"),
    "barbell row": ("ROW", "BARBELL_ROW"),
    "remo inclinado": ("ROW", "BENT_OVER_ROW_WITH_BARBELL"),
    "remo inclinado barra": ("ROW", "BENT_OVER_ROW_WITH_BARBELL"),
    "remo con mancuerna": ("ROW", "DUMBBELL_ROW"),
    "remo con mancuernas": ("ROW", "DUMBBELL_ROW"),
    "remo mancuerna": ("ROW", "DUMBBELL_ROW"),
    "remo mancuernas": ("ROW", "DUMBBELL_ROW"),
    "dumbbell row": ("ROW", "DUMBBELL_ROW"),
    "remo sentado": ("ROW", "SEATED_CABLE_ROW"),
    "remo en polea": ("ROW", "SEATED_CABLE_ROW"),
    "remo polea baja": ("ROW", "SEATED_CABLE_ROW"),
    "remo gironda": ("ROW", "SEATED_CABLE_ROW"),
    "seated cable row": ("ROW", "SEATED_CABLE_ROW"),
    "remo en t": ("ROW", "T_BAR_ROW"),
    "remo t": ("ROW", "T_BAR_ROW"),
    "remo": ("ROW", "DUMBBELL_ROW"),
    "row": ("ROW", "DUMBBELL_ROW"),
    "jalon": ("PULL_UP", "LAT_PULLDOWN"),
    "jalón": ("PULL_UP", "LAT_PULLDOWN"),
    "jalon al pecho": ("PULL_UP", "LAT_PULLDOWN"),
    "jalón al pecho": ("PULL_UP", "LAT_PULLDOWN"),
    "jalon polea": ("PULL_UP", "LAT_PULLDOWN"),
    "lat pulldown": ("PULL_UP", "LAT_PULLDOWN"),
    "pulldown": ("PULL_UP", "LAT_PULLDOWN"),
    "dominadas": ("PULL_UP", "PULL_UP"),
    "dominada": ("PULL_UP", "PULL_UP"),
    "pull up": ("PULL_UP", "PULL_UP"),
    "pullup": ("PULL_UP", "PULL_UP"),
    "pullups": ("PULL_UP", "PULL_UP"),
    "chin up": ("PULL_UP", "CHIN_UP"),
    "chinup": ("PULL_UP", "CHIN_UP"),
    "face pull": ("ROW", "FACE_PULL"),
    "facepull": ("ROW", "FACE_PULL"),
    "pullover polea": ("PULL_UP", "STRAIGHT_ARM_PULLDOWN"),
    "hiperextensiones": ("HYPEREXTENSION", "HYPEREXTENSION"),
    "encogimiento de hombros": ("SHRUG", "BARBELL_SHRUG"),
    "encogimiento hombros barra": ("SHRUG", "BARBELL_SHRUG"),
    "encogimiento hombros mancuernas": ("SHRUG", "DUMBBELL_SHRUG"),
    "shrug": ("SHRUG", "BARBELL_SHRUG"),

    # ── HOMBRO / SHOULDERS ──
    "press militar": ("SHOULDER_PRESS", "OVERHEAD_BARBELL_PRESS"),
    "press militar barra": ("SHOULDER_PRESS", "OVERHEAD_BARBELL_PRESS"),
    "press por encima de la cabeza con barra": ("SHOULDER_PRESS", "OVERHEAD_BARBELL_PRESS"),
    "overhead barbell press": ("SHOULDER_PRESS", "OVERHEAD_BARBELL_PRESS"),
    "press hombro": ("SHOULDER_PRESS", "OVERHEAD_DUMBBELL_PRESS"),
    "press hombros": ("SHOULDER_PRESS", "OVERHEAD_DUMBBELL_PRESS"),
    "press con mancuernas por encima de la cabeza": ("SHOULDER_PRESS", "OVERHEAD_DUMBBELL_PRESS"),
    "press hombro mancuernas": ("SHOULDER_PRESS", "OVERHEAD_DUMBBELL_PRESS"),
    "shoulder press": ("SHOULDER_PRESS", "OVERHEAD_DUMBBELL_PRESS"),
    "press arnold": ("SHOULDER_PRESS", "ARNOLD_PRESS"),
    "arnold press": ("SHOULDER_PRESS", "ARNOLD_PRESS"),
    "elevaciones laterales": ("LATERAL_RAISE", "DUMBBELL_LATERAL_RAISE"),
    "elevacion lateral": ("LATERAL_RAISE", "DUMBBELL_LATERAL_RAISE"),
    "elevación lateral": ("LATERAL_RAISE", "DUMBBELL_LATERAL_RAISE"),
    "lateral raise": ("LATERAL_RAISE", "DUMBBELL_LATERAL_RAISE"),
    "elevaciones frontales": ("SHOULDER_PRESS", "DUMBBELL_FRONT_RAISE"),
    "elevacion frontal": ("SHOULDER_PRESS", "DUMBBELL_FRONT_RAISE"),
    "front raise": ("SHOULDER_PRESS", "DUMBBELL_FRONT_RAISE"),
    "pajaros": ("LATERAL_RAISE", "REAR_DELT_RAISE"),
    "pájaros": ("LATERAL_RAISE", "REAR_DELT_RAISE"),
    "pajaros hombro": ("LATERAL_RAISE", "REAR_DELT_RAISE"),
    "remo al menton": ("SHOULDER_PRESS", "UPRIGHT_ROW"),
    "remo al mentón": ("SHOULDER_PRESS", "UPRIGHT_ROW"),

    # ── BRAZOS / ARMS ──
    "curl de bíceps con barra": ("CURL", "BARBELL_BICEPS_CURL"),
    "curl biceps barra": ("CURL", "BARBELL_BICEPS_CURL"),
    "curl bíceps barra": ("CURL", "BARBELL_BICEPS_CURL"),
    "barbell biceps curl": ("CURL", "BARBELL_BICEPS_CURL"),
    "curl de bíceps con mancuerna": ("CURL", "DUMBBELL_BICEPS_CURL"),
    "curl de bíceps con mancuernas": ("CURL", "STANDING_DUMBBELL_BICEPS_CURL"),
    "curl mancuerna": ("CURL", "DUMBBELL_BICEPS_CURL"),
    "curl mancuernas": ("CURL", "STANDING_DUMBBELL_BICEPS_CURL"),
    "dumbbell biceps curl": ("CURL", "DUMBBELL_BICEPS_CURL"),
    "curl biceps": ("CURL", "BICEPS_CURL"),
    "curl bíceps": ("CURL", "BICEPS_CURL"),
    "biceps curl": ("CURL", "BICEPS_CURL"),
    "curl martillo": ("CURL", "HAMMER_CURL"),
    "hammer curl": ("CURL", "HAMMER_CURL"),
    "curl concentrado": ("CURL", "CONCENTRATION_CURL"),
    "curl predicador": ("CURL", "PREACHER_CURL"),
    "curl scott": ("CURL", "PREACHER_CURL"),
    "curl polea": ("CURL", "CABLE_CURL"),
    "curl": ("CURL", "BICEPS_CURL"),
    "extension triceps polea": ("TRICEPS_EXTENSION", "TRICEPS_PRESSDOWN"),
    "extensión tríceps polea": ("TRICEPS_EXTENSION", "TRICEPS_PRESSDOWN"),
    "jalon triceps": ("TRICEPS_EXTENSION", "TRICEPS_PRESSDOWN"),
    "jalón tríceps": ("TRICEPS_EXTENSION", "TRICEPS_PRESSDOWN"),
    "triceps pressdown": ("TRICEPS_EXTENSION", "TRICEPS_PRESSDOWN"),
    "extension triceps": ("TRICEPS_EXTENSION", "TRICEPS_EXTENSION"),
    "extensión tríceps": ("TRICEPS_EXTENSION", "TRICEPS_EXTENSION"),
    "extension de triceps": ("TRICEPS_EXTENSION", "TRICEPS_EXTENSION"),
    "extensión de tríceps": ("TRICEPS_EXTENSION", "TRICEPS_EXTENSION"),
    "triceps extension": ("TRICEPS_EXTENSION", "TRICEPS_EXTENSION"),
    "extension tras nuca": ("TRICEPS_EXTENSION", "OVERHEAD_DUMBBELL_TRICEPS_EXTENSION"),
    "press frances": ("TRICEPS_EXTENSION", "SKULL_CRUSHER"),
    "press francés": ("TRICEPS_EXTENSION", "SKULL_CRUSHER"),
    "fondos triceps": ("DIP", "BENCH_DIP"),
    "fondos tríceps": ("DIP", "BENCH_DIP"),
    "fondos en banco": ("DIP", "BENCH_DIP"),
    "dips": ("DIP", "CHEST_DIP"),

    # ── PIERNAS Y GLÚTEO / LEGS & GLUTES ──
    "sentadilla trasera": ("SQUAT", "BARBELL_BACK_SQUAT"),
    "sentadilla con barra": ("SQUAT", "BARBELL_BACK_SQUAT"),
    "sentadilla barra": ("SQUAT", "BARBELL_BACK_SQUAT"),
    "barbell back squat": ("SQUAT", "BARBELL_BACK_SQUAT"),
    "sentadilla con mancuernas": ("SQUAT", "DUMBBELL_SQUAT"),
    "sentadilla mancuernas": ("SQUAT", "DUMBBELL_SQUAT"),
    "dumbbell squat": ("SQUAT", "DUMBBELL_SQUAT"),
    "sentadilla goblet": ("SQUAT", "GOBLET_SQUAT"),
    "goblet squat": ("SQUAT", "GOBLET_SQUAT"),
    "sentadilla frontal": ("SQUAT", "FRONT_SQUAT"),
    "front squat": ("SQUAT", "FRONT_SQUAT"),
    "sentadilla bulgara": ("LUNGE", "BULGARIAN_SPLIT_SQUAT"),
    "sentadilla búlgara": ("LUNGE", "BULGARIAN_SPLIT_SQUAT"),
    "bulgarian split squat": ("LUNGE", "BULGARIAN_SPLIT_SQUAT"),
    "sentadilla": ("SQUAT", "SQUAT"),
    "sentadillas": ("SQUAT", "SQUAT"),
    "squat": ("SQUAT", "SQUAT"),
    "squats": ("SQUAT", "SQUAT"),
    "prensa": ("SQUAT", "LEG_PRESS"),
    "prensa de piernas": ("SQUAT", "LEG_PRESS"),
    "prensa piernas": ("SQUAT", "LEG_PRESS"),
    "prensa inclinada": ("SQUAT", "LEG_PRESS"),
    "prensa 45": ("SQUAT", "LEG_PRESS"),
    "leg press": ("SQUAT", "LEG_PRESS"),
    "incline leg press": ("SQUAT", "LEG_PRESS"),
    "extension cuadriceps": ("LEG_CURL", "LEG_EXTENSION"),
    "extensión cuádriceps": ("LEG_CURL", "LEG_EXTENSION"),
    "extension de cuadriceps": ("LEG_CURL", "LEG_EXTENSION"),
    "extensiones de cuadriceps": ("LEG_CURL", "LEG_EXTENSION"),
    "extensiones cuadriceps": ("LEG_CURL", "LEG_EXTENSION"),
    "leg extension": ("LEG_CURL", "LEG_EXTENSION"),
    "curl femoral": ("LEG_CURL", "LEG_CURL"),
    "curl femoral tumbado": ("LEG_CURL", "LEG_CURL"),
    "curl femoral sentado": ("LEG_CURL", "SEATED_LEG_CURL"),
    "curl de piernas": ("LEG_CURL", "LEG_CURL"),
    "leg curl": ("LEG_CURL", "LEG_CURL"),
    "zancadas caminando": ("LUNGE", "WALKING_LUNGE"),
    "zancada caminando": ("LUNGE", "WALKING_LUNGE"),
    "zancadas andadas": ("LUNGE", "WALKING_LUNGE"),
    "walking lunge": ("LUNGE", "WALKING_LUNGE"),
    "walking lunges": ("LUNGE", "WALKING_LUNGE"),
    "zancadas con mancuernas": ("LUNGE", "DUMBBELL_LUNGE"),
    "zancadas mancuernas": ("LUNGE", "DUMBBELL_LUNGE"),
    "dumbbell lunge": ("LUNGE", "DUMBBELL_LUNGE"),
    "zancadas": ("LUNGE", "DUMBBELL_LUNGE"),
    "zancada": ("LUNGE", "DUMBBELL_LUNGE"),
    "lunges": ("LUNGE", "DUMBBELL_LUNGE"),
    "lunge": ("LUNGE", "DUMBBELL_LUNGE"),
    "peso muerto con barra": ("DEADLIFT", "BARBELL_DEADLIFT"),
    "peso muerto barra": ("DEADLIFT", "BARBELL_DEADLIFT"),
    "barbell deadlift": ("DEADLIFT", "BARBELL_DEADLIFT"),
    "peso muerto con mancuernas": ("DEADLIFT", "DUMBBELL_DEADLIFT"),
    "peso muerto mancuernas": ("DEADLIFT", "DUMBBELL_DEADLIFT"),
    "dumbbell deadlift": ("DEADLIFT", "DUMBBELL_DEADLIFT"),
    "peso muerto rumano": ("DEADLIFT", "ROMANIAN_DEADLIFT"),
    "romanian deadlift": ("DEADLIFT", "ROMANIAN_DEADLIFT"),
    "peso muerto sumo": ("DEADLIFT", "SUMO_DEADLIFT"),
    "peso muerto": ("DEADLIFT", "BARBELL_DEADLIFT"),
    "deadlift": ("DEADLIFT", "BARBELL_DEADLIFT"),
    "levantamiento de barra sobre cadera, en banca": ("HIP_RAISE", "BARBELL_HIP_THRUST_WITH_BENCH"),
    "hip thrust con barra": ("HIP_RAISE", "BARBELL_HIP_THRUST_WITH_BENCH"),
    "hip thrust": ("HIP_RAISE", "BARBELL_HIP_THRUST_WITH_BENCH"),
    "puente de gluteo": ("HIP_RAISE", "GLUTE_BRIDGE"),
    "puente de glúteo": ("HIP_RAISE", "GLUTE_BRIDGE"),
    "puente gluteo": ("HIP_RAISE", "GLUTE_BRIDGE"),
    "glute bridge": ("HIP_RAISE", "GLUTE_BRIDGE"),
    "elevación de talones de pie con barra": ("CALF_RAISE", "STANDING_BARBELL_CALF_RAISE"),
    "elevacion talones barra": ("CALF_RAISE", "STANDING_BARBELL_CALF_RAISE"),
    "gemelos de pie": ("CALF_RAISE", "STANDING_BARBELL_CALF_RAISE"),
    "gemelos sentado": ("CALF_RAISE", "SEATED_CALF_RAISE"),
    "gemelos": ("CALF_RAISE", "STANDING_CALF_RAISE"),
    "elevacion talones": ("CALF_RAISE", "STANDING_CALF_RAISE"),
    "calf raise": ("CALF_RAISE", "STANDING_CALF_RAISE"),

    # ── CORE / ABDOMEN ──
    "plank": ("PLANK", "PLANK"),
    "plancha": ("PLANK", "PLANK"),
    "plancha abdominal": ("PLANK", "PLANK"),
    "plancha frontal": ("PLANK", "PLANK"),
    "plancha lateral": ("PLANK", "SIDE_PLANK"),
    "side plank": ("PLANK", "SIDE_PLANK"),
    "abdominales": ("CRUNCH", "CRUNCH"),
    "crunch": ("CRUNCH", "CRUNCH"),
    "crunch abdominal": ("CRUNCH", "CRUNCH"),
    "crunch en polea": ("CRUNCH", "CABLE_CRUNCH"),
    "sit ups": ("SIT_UP", "SIT_UP"),
    "sit up": ("SIT_UP", "SIT_UP"),
    "situps": ("SIT_UP", "SIT_UP"),
    "rueda abdominal": ("CRUNCH", "AB_WHEEL"),
    "ab wheel": ("CRUNCH", "AB_WHEEL"),
    "elevacion piernas": ("CRUNCH", "LEG_RAISE"),
    "elevación de piernas": ("CRUNCH", "LEG_RAISE"),
    "leg raise": ("CRUNCH", "LEG_RAISE"),
    "russian twist": ("CRUNCH", "RUSSIAN_TWIST"),
    "giros rusos": ("CRUNCH", "RUSSIAN_TWIST"),
    "deadbug": ("CRUNCH", "DEAD_BUG"),
    "dead bug": ("CRUNCH", "DEAD_BUG"),
    "dead bugs": ("CRUNCH", "DEAD_BUG"),
    "dead-bug": ("CRUNCH", "DEAD_BUG"),
    "bicho muerto": ("CRUNCH", "DEAD_BUG"),
    "bichos muertos": ("CRUNCH", "DEAD_BUG"),
    "bird dog": ("PLANK", "BIRD_DOG"),
    "bird-dog": ("PLANK", "BIRD_DOG"),
    "perro pajaro": ("PLANK", "BIRD_DOG"),

    # ── OLÍMPICOS Y FUNCIONAL / CROSSFIT ──
    "arrancada con barra de pesas": ("SNATCH", "BARBELL_SNATCH"),
    "arrancada con barra": ("SNATCH", "BARBELL_SNATCH"),
    "arrancada": ("SNATCH", "BARBELL_SNATCH"),
    "snatch": ("SNATCH", "BARBELL_SNATCH"),
    "cargada con barra": ("CLEAN", "CLEAN"),
    "cargada": ("CLEAN", "CLEAN"),
    "clean": ("CLEAN", "CLEAN"),
    "kettlebell swing": ("TOTAL_BODY", "KETTLEBELL_SWING"),
    "swing kettlebell": ("TOTAL_BODY", "KETTLEBELL_SWING"),
    "burpees": ("CARDIO", "BURPEE"),
    "burpee": ("CARDIO", "BURPEE"),
    "salto al cajon": ("TOTAL_BODY", "BOX_JUMP"),
    "box jump": ("TOTAL_BODY", "BOX_JUMP"),
    "thruster": ("TOTAL_BODY", "THRUSTER"),
}


def resolve_exercise(name: str):
    """Resuelve un nombre de ejercicio a su (category, exerciseName) oficial de Garmin Connect."""
    if not name:
        return "OTHER", ""
    clean = name.strip().lower()

    # 1. Coincidencia exacta en el diccionario
    if clean in EXERCISE_MAP:
        return EXERCISE_MAP[clean]

    # 2. Coincidencia por contención de subcadenas
    for k, v in EXERCISE_MAP.items():
        if k in clean or clean in k:
            return v

    # 3. Fallback inteligente por palabras clave para garantizar categoría oficial de Garmin
    if "remo" in clean or "row" in clean:
        return ("ROW", "DUMBBELL_ROW")
    if "jalon" in clean or "jalón" in clean or "pulldown" in clean:
        return ("PULL_UP", "LAT_PULLDOWN")
    if "dominada" in clean or "pull up" in clean or "pullup" in clean:
        return ("PULL_UP", "PULL_UP")
    if "press" in clean and ("banca" in clean or "pecho" in clean or "chest" in clean or "bench" in clean):
        return ("BENCH_PRESS", "DUMBBELL_BENCH_PRESS")
    if "flexion" in clean or "flexión" in clean or "pushup" in clean or "push up" in clean:
        return ("PUSH_UP", "PUSH_UP")
    if "biceps" in clean or "bíceps" in clean or "curl" in clean:
        return ("CURL", "STANDING_DUMBBELL_BICEPS_CURL")
    if "triceps" in clean or "tríceps" in clean or "polea" in clean:
        return ("TRICEPS_EXTENSION", "TRICEPS_PRESSDOWN")
    if "bulgara" in clean or "búlgara" in clean:
        return ("LUNGE", "BULGARIAN_SPLIT_SQUAT")
    if "sentadilla" in clean or "squat" in clean:
        return ("SQUAT", "BARBELL_BACK_SQUAT")
    if "prensa" in clean or "leg press" in clean:
        return ("LEG_PRESS", "LEG_PRESS")
    if "cuadricep" in clean or "cuádricep" in clean:
        return ("LEG_CURL", "LEG_EXTENSION")
    if "femoral" in clean or "isquio" in clean:
        return ("LEG_CURL", "LEG_CURL")
    if "peso muerto" in clean or "deadlift" in clean:
        return ("DEADLIFT", "BARBELL_DEADLIFT")
    if "zancada" in clean or "lunge" in clean:
        return ("LUNGE", "DUMBBELL_LUNGE")
    if "hip thrust" in clean or "glute" in clean or "glúteo" in clean:
        return ("HIP_RAISE", "BARBELL_HIP_THRUST_WITH_BENCH")
    if "gemelo" in clean or "calf" in clean or "talon" in clean or "talón" in clean:
        return ("CALF_RAISE", "STANDING_BARBELL_CALF_RAISE")
    if "plank" in clean or "plancha" in clean:
        return ("PLANK", "PLANK")
    if "hombro" in clean or "shoulder" in clean or "militar" in clean or "arnold" in clean:
        return ("SHOULDER_PRESS", "OVERHEAD_DUMBBELL_PRESS")
    if "lateral" in clean or "pajaro" in clean or "pájaro" in clean or "frontal" in clean:
        return ("LATERAL_RAISE", "DUMBBELL_LATERAL_RAISE")
    if "shrug" in clean or "trapecio" in clean or "encogimiento" in clean:
        return ("SHRUG", "BARBELL_SHRUG")
    if "abdomina" in clean or "crunch" in clean or "sit up" in clean or "situp" in clean:
        return ("CRUNCH", "CRUNCH")
    if "snatch" in clean or "arrancada" in clean:
        return ("SNATCH", "BARBELL_SNATCH")
    if "clean" in clean or "cargada" in clean:
        return ("CLEAN", "CLEAN")

    # Si todo falla, devolver categoría genérica de fuerza para que nunca quede vacío
    return ("SQUAT", "")


def parse_strength_text(text: str) -> List[Dict[str, Any]]:
    """Parsea texto libre con ejercicios de fuerza a una lista de diccionarios estructurados."""
    import re
    exercises = []
    if not text:
        return exercises

    lines = [l.strip() for l in text.replace(";", "\n").split("\n") if l.strip()]
    for line in lines:
        clean_line = re.sub(r'^[•\-\*\d\.\)\s]+', '', line).strip()
        if not clean_line or len(clean_line) < 3:
            continue

        rest_sec = 60
        rest_match = re.search(r'(\d+)\s*s(?:eg)?\s*(?:rest|descanso)|(?:rest|descanso)\s*[:=]?\s*(\d+)\s*s?', clean_line, re.IGNORECASE)
        if rest_match:
            rest_sec = int(rest_match.group(1) or rest_match.group(2))
            clean_line = re.sub(r'[\·\|\,\-]?\s*(\d+\s*s(?:eg)?\s*(?:rest|descanso)|(?:rest|descanso)\s*[:=]?\s*\d+\s*s?)', '', clean_line, flags=re.IGNORECASE).strip()

        # Patrón 3x10 o 3x45s
        m = re.search(r'(\d+)\s*[xX*×]\s*(\d+)\s*(s|seg|segundos|reps?|repeticiones)?', clean_line, re.IGNORECASE)
        if m:
            sets = int(m.group(1))
            val = int(m.group(2))
            unit = (m.group(3) or '').lower()
            ex_name = clean_line[:m.start()].strip(' :-·|,\t')
            if not ex_name:
                ex_name = clean_line[m.end():].strip(' :-·|,\t')

            is_time = unit.startswith('s') or 'plank' in ex_name.lower() or 'plancha' in ex_name.lower()
            ex_dict = {'name': ex_name or clean_line, 'sets': sets, 'rest_seconds': rest_sec}
            if is_time:
                ex_dict['seconds'] = val
            else:
                ex_dict['reps'] = val
            exercises.append(ex_dict)
            continue

        # Patrón 3 series de 10 reps
        m2 = re.search(r'(\d+)\s*series?\s*(?:de|x)?\s*(\d+)\s*(s|seg|segundos|reps?|repeticiones)?', clean_line, re.IGNORECASE)
        if m2:
            sets = int(m2.group(1))
            val = int(m2.group(2))
            unit = (m2.group(3) or '').lower()
            ex_name = clean_line[:m2.start()].strip(' :-·|,\t')
            if not ex_name:
                ex_name = clean_line[m2.end():].strip(' :-·|,\t')

            is_time = unit.startswith('s') or 'plank' in ex_name.lower() or 'plancha' in ex_name.lower()
            ex_dict = {'name': ex_name or clean_line, 'sets': sets, 'rest_seconds': rest_sec}
            if is_time:
                ex_dict['seconds'] = val
            else:
                ex_dict['reps'] = val
            exercises.append(ex_dict)
            continue

        # Patrón '10 repeticiones de sentadilla' o '10 reps sentadillas' o '10 sentadillas'
        m3 = re.search(r'^(\d+)\s*(?:reps?|repeticiones)?\s*(?:de\s+)?([a-záéíóúñ\s\-_]+)$', clean_line, re.IGNORECASE)
        if m3:
            val = int(m3.group(1))
            ex_name = m3.group(2).strip(' :-·|,\t')
            ex_name = re.sub(r'^(?:reps?|repeticiones)\s*(?:de\s+)?', '', ex_name, flags=re.IGNORECASE).strip()
            is_time = 'plank' in ex_name.lower() or 'plancha' in ex_name.lower()
            ex_dict = {'name': ex_name, 'sets': 1, 'rest_seconds': rest_sec}
            if is_time:
                ex_dict['seconds'] = val
            else:
                ex_dict['reps'] = val
            exercises.append(ex_dict)
            continue

        exercises.append({'name': clean_line, 'sets': 1, 'reps': 10, 'rest_seconds': rest_sec})

    return exercises


def build_strength_json(
    name: str,
    exercises: List[Dict[str, Any]],
) -> dict:
    """Build the Garmin Connect JSON for a strength workout with RepeatGroupDTO and official exercise recognition."""
    steps: List[dict] = []
    step_order = 1

    for ex in exercises:
        ex_name = ex.get("name", "Exercise")
        sets = int(ex.get("sets", 1))
        reps = ex.get("reps")
        duration_sec = ex.get("seconds") or ex.get("duration_seconds")
        rest_seconds = int(ex.get("rest_seconds", 60))

        # Detectar si es por tiempo (ej. Planchas de 30s) o por repeticiones
        is_time_based = bool(duration_sec or "plank" in ex_name.lower() or "plancha" in ex_name.lower())
        target_val = float(duration_sec or reps or (30 if is_time_based else 10))

        category, official_ex_name = resolve_exercise(ex_name)

        # Paso de trabajo de la serie (con animación oficial de Garmin)
        work_step = {
            "type": "ExecutableStepDTO",
            "stepOrder": step_order + 1,
            "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
            "description": None,
            "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
            "strokeType": {"strokeTypeId": 0, "strokeTypeKey": None, "displayOrder": 0},
            "equipmentType": {"equipmentTypeId": 0, "equipmentTypeKey": None, "displayOrder": 0},
            "weightValue": None,
            "weightUnit": {"unitId": 8, "unitKey": "kilogram", "factor": 1000.0},
        }

        if is_time_based:
            work_step["endCondition"] = {"conditionTypeId": 2, "conditionTypeKey": "time"}
            work_step["endConditionValue"] = target_val
        else:
            work_step["endCondition"] = {"conditionTypeId": 10, "conditionTypeKey": "reps"}
            work_step["endConditionValue"] = target_val

        if category:
            work_step["category"] = category
        if official_ex_name:
            work_step["exerciseName"] = official_ex_name

        inner_steps = [work_step]

        # Paso de descanso entre series (tipo "rest" integrado en el ejercicio)
        if rest_seconds > 0:
            rest_step = {
                "type": "ExecutableStepDTO",
                "stepOrder": step_order + 2,
                "stepType": {"stepTypeId": 5, "stepTypeKey": "rest"},
                "description": None,
                "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                "endConditionValue": float(rest_seconds),
                "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
                "strokeType": {"strokeTypeId": 0, "strokeTypeKey": None, "displayOrder": 0},
                "equipmentType": {"equipmentTypeId": 0, "equipmentTypeKey": None, "displayOrder": 0},
                "weightValue": None,
                "weightUnit": {"unitId": 8, "unitKey": "kilogram", "factor": 1000.0},
            }
            inner_steps.append(rest_step)

        # Encapsular SIEMPRE con RepeatGroupDTO para que Garmin Connect active la tarjeta oficial y los vídeos
        group = {
            "type": "RepeatGroupDTO",
            "stepOrder": step_order,
            "stepType": {"stepTypeId": 6, "stepTypeKey": "repeat"},
            "numberOfIterations": sets,
            "endCondition": {"conditionTypeId": 7, "conditionTypeKey": "iterations"},
            "endConditionValue": float(sets),
            "skipLastRestStep": False,
            "smartRepeat": False,
            "workoutSteps": inner_steps,
        }
        steps.append(group)
        step_order += 1 + len(inner_steps)

    return {
        "workoutName": name,
        "description": None,
        "workoutProvider": "Garmin",
        "workoutSourceId": "GGtMeLu",
        "sportType": {"sportTypeId": 5, "sportTypeKey": "strength_training"},
        "workoutSegments": [{
            "segmentOrder": 1,
            "sportType": {"sportTypeId": 5, "sportTypeKey": "strength_training"},
            "workoutSteps": steps,
        }],
    }


# =============================================================================
# MCP TOOLS
# =============================================================================

def register_tools(app):
    """Register all high-level workout builder tools with the MCP server app"""

    @app.tool()
    async def create_walk_run_workout(
        name: str,
        run_seconds: int,
        walk_seconds: int,
        repeats: int,
        warmup_min: int,
        cooldown_min: int,
        hr_zone: str = "Z3",
    ) -> str:
        """Create a walk/run interval workout and upload it to Garmin Connect.

        Builds the internal Garmin JSON automatically and returns the new workout ID.

        Args:
            name: Workout name (e.g. "W3 Mié 2:2")
            run_seconds: Duration of each run interval in seconds
            walk_seconds: Duration of each walk/recovery interval in seconds
            repeats: Number of run/walk repetitions
            warmup_min: Warmup duration in minutes
            cooldown_min: Cooldown duration in minutes
            hr_zone: Target heart-rate zone (Z1-Z5, default Z3)
        """
        try:
            workout_json = build_walk_run_json(
                name=name,
                run_seconds=run_seconds,
                walk_seconds=walk_seconds,
                repeats=repeats,
                warmup_min=warmup_min,
                cooldown_min=cooldown_min,
                hr_zone=hr_zone,
            )
            result = garmin_client.upload_workout(workout_json)

            if isinstance(result, dict):
                curated = {
                    "status": "success",
                    "workout_id": result.get("workoutId"),
                    "name": result.get("workoutName"),
                    "message": "Workout uploaded successfully",
                }
                curated = {k: v for k, v in curated.items() if v is not None}
                return json.dumps(curated, indent=2)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error creating walk/run workout: {str(e)}"

    @app.tool()
    async def create_run_workout(
        name: str,
        run_seconds: int,
        warmup_min: int,
        cooldown_min: int,
        hr_zone: str = "Z3",
    ) -> str:
        """Create a continuous run workout and upload it to Garmin Connect.

        Builds a single uninterrupted run interval with warmup and cooldown walks.

        Args:
            name: Workout name (e.g. "Step 8 - 30min continuous")
            run_seconds: Duration of the run in seconds
            warmup_min: Warmup walk duration in minutes
            cooldown_min: Cooldown walk duration in minutes
            hr_zone: Target heart-rate zone (Z1-Z5, default Z3)
        """
        try:
            workout_json = build_run_json(
                name=name,
                run_seconds=run_seconds,
                warmup_min=warmup_min,
                cooldown_min=cooldown_min,
                hr_zone=hr_zone,
            )
            result = garmin_client.upload_workout(workout_json)

            if isinstance(result, dict):
                curated = {
                    "status": "success",
                    "workout_id": result.get("workoutId"),
                    "name": result.get("workoutName"),
                    "message": "Workout uploaded successfully",
                }
                curated = {k: v for k, v in curated.items() if v is not None}
                return json.dumps(curated, indent=2)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error creating run workout: {str(e)}"

    @app.tool()
    async def create_z2_walk_workout(
        name: str,
        duration_min: int,
        hr_min: int,
        hr_max: int,
    ) -> str:
        """Create a steady Z2 walking workout and upload it to Garmin Connect.

        Args:
            name: Workout name
            duration_min: Main walking block duration in minutes
            hr_min: Minimum heart rate in bpm (used for description; target is Z2)
            hr_max: Maximum heart rate in bpm (used for description; target is Z2)
        """
        try:
            workout_json = build_z2_walk_json(
                name=name,
                duration_min=duration_min,
                hr_min=hr_min,
                hr_max=hr_max,
            )
            result = garmin_client.upload_workout(workout_json)

            if isinstance(result, dict):
                curated = {
                    "status": "success",
                    "workout_id": result.get("workoutId"),
                    "name": result.get("workoutName"),
                    "message": "Workout uploaded successfully",
                }
                curated = {k: v for k, v in curated.items() if v is not None}
                return json.dumps(curated, indent=2)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error creating Z2 walk workout: {str(e)}"

    @app.tool()
    async def create_strength_workout(
        name: str,
        exercises: List[Dict[str, Any]],
    ) -> str:
        """Create a strength workout with native Garmin 3D animations and mobile videos, and upload it to Garmin Connect.

        The server automatically resolves exercise names (in Spanish or English) to Garmin's official catalog
        with grouped RepeatGroupDTO sets, integrated rest intervals, and official multimedia provider IDs.
        Pass standard exercise names like 'Sentadilla con barra', 'Prensa de piernas', 'Dead bug', 'Jalón al pecho',
        'Zancadas caminando', 'Plancha', etc.

        Args:
            name: Workout name (e.g. "Pierna + Core")
            exercises: List of dicts with keys: name (str), sets (int), reps (int) or seconds (int), rest_seconds (int)
        """
        try:
            workout_json = build_strength_json(name=name, exercises=exercises)
            result = garmin_client.upload_workout(workout_json)

            if isinstance(result, dict):
                curated = {
                    "status": "success",
                    "workout_id": result.get("workoutId"),
                    "name": result.get("workoutName"),
                    "message": "Workout uploaded successfully",
                }
                curated = {k: v for k, v in curated.items() if v is not None}
                return json.dumps(curated, indent=2)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error creating strength workout: {str(e)}"

    @app.tool()
    async def schedule_week(week: List[Dict[str, Any]]) -> str:
        """Schedule a list of workouts for the week in a single call.

        Idempotent: if a workout is already scheduled for that date, it is
        reported as already scheduled and the POST is skipped (avoids
        duplicating calendar entries).

        Args:
            week: List of dicts with keys: date (YYYY-MM-DD), workout_id (int)
        """
        # Imported here (not at module top) to avoid any import-time ordering
        # surprises between sibling modules. Both modules share the same
        # garmin_client instance via configure() in __main__.
        from garmin_mcp.workouts import _is_already_scheduled

        try:
            results = []
            for item in week:
                calendar_date = item["date"]
                workout_id = int(item["workout_id"])

                if _is_already_scheduled(workout_id, calendar_date):
                    results.append({
                        "date": calendar_date,
                        "workout_id": workout_id,
                        "status": "already_scheduled",
                        "idempotent": True,
                    })
                    continue

                # garminconnect 0.3.2 dropped the .garth attribute; use .client.
                url = f"workout-service/schedule/{workout_id}"
                response = garmin_client.client.post(
                    "connectapi", url, json={"date": calendar_date}
                )
                if response.status_code == 200:
                    results.append({
                        "date": calendar_date,
                        "workout_id": workout_id,
                        "status": "scheduled",
                    })
                else:
                    results.append({
                        "date": calendar_date,
                        "workout_id": workout_id,
                        "status": "failed",
                        "http_status": response.status_code,
                    })
            return json.dumps({
                "status": "complete",
                "scheduled": results,
            }, indent=2)
        except Exception as e:
            return f"Error scheduling week: {str(e)}"

    return app
