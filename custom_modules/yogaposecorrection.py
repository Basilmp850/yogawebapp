from math import degrees
from math import atan2

# import pandas as pd

# df = pd.read_csv('../samplecsv.csv')
def calculateAngle(landmark1, landmark2, landmark3):
    '''
    This function calculates angle between three different landmarks.
    Args:
        landmark1: The first landmark containing the x,y and z coordinates.
        landmark2: The second landmark containing the x,y and z coordinates.
        landmark3: The third landmark containing the x,y and z coordinates.
    Returns:
        angle: The calculated angle between the three landmarks.
 
    '''
 
    # Get the required landmarks coordinates.
    x1, y1, _ = landmark1
    x2, y2, _ = landmark2
    x3, y3, _ = landmark3
 
    # Calculate the angle between the three points
    angle = degrees(atan2(y3 - y2, x3 - x2) - atan2(y1 - y2, x1 - x2))
    
    # Check if the angle is less than zero.
    if angle < 0:
 
        # Add 360 to the found angle.
        angle += 360
        print("negative")
    
    # Return the calculated angle.
    return angle

#Format for calculating angle
angle = calculateAngle((558, 326, 0), (642, 333, 0), (718, 321, 0))


#Warrior 11,Tree and T pose

# Get the angle between the left shoulder, elbow and wrist points. 

'''
 calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value],
                                      landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value],
                                      landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value])
'''
def left_elbow_angle(X,Y,Z): 
   return calculateAngle(X,Y,Z)

find_angle = lambda X,Y,Z : calculateAngle(X,Y,Z)


# print(find_angle((df['LEFT_SHOULDER_x'], df['LEFT_SHOULDER_y'], 0), (df['LEFT_ELBOW_x'], df['LEFT_ELBOW_y'], 0), (df['LEFT_WRIST_x'], df['LEFT_WRIST_y'], 0)))

    
#     # Get the angle between the right shoulder, elbow and wrist points. 
# right_elbow_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
#                                        landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value],
#                                        landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value])   
    
#     # Get the angle between the left elbow, shoulder and hip points. 
# left_shoulder_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value],
#                                          landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value],
#                                          landmarks[mp_pose.PoseLandmark.LEFT_HIP.value])

#     # Get the angle between the right hip, shoulder and elbow points. 
# right_shoulder_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value],
#                                           landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value],
#                                           landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value])

#     # Get the angle between the left hip, knee and ankle points. 
# left_knee_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.LEFT_HIP.value],
#                                      landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value],
#                                      landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value])

#     # Get the angle between the right hip, knee and ankle points 
# right_knee_angle = calculateAngle(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value],
#                                       landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value],
#                                       landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value])

'''
Warrior 11 pose

    Around 180° at both elbows
    Around 90° angle at both shoulders
    Around 180° angle at one knee
    Around 90° angle at the other knee
    Left leg straight 
    Right leg ben at an angle between 90 and 120 degree

'''

#define correction commands for each pose specifically.

#Tree Pose
def standardize(x):
    if x>190:
        return 360-x
    return x

def tree_pose_correction(df):
    command=""
    left_hip_angle = (find_angle((df['LEFT_SHOULDER_x'],df['LEFT_SHOULDER_y'],0),(df['LEFT_HIP_x'], df['LEFT_HIP_y'],0),(df['LEFT_KNEE_x'],df['LEFT_KNEE_y'],0)))
    right_knee_angle = standardize(find_angle((df['RIGHT_ANKLE_x'],df['RIGHT_ANKLE_y'],0),(df['RIGHT_KNEE_x'], df['RIGHT_KNEE_y'],0),(df['RIGHT_HIP_x'],df['RIGHT_HIP_y'],0)))
    right_hip_angle = (find_angle((df['RIGHT_KNEE_x'],df['RIGHT_KNEE_y'],0),(df['RIGHT_HIP_x'], df['RIGHT_HIP_y'],0),(df['RIGHT_SHOULDER_x'],df['RIGHT_SHOULDER_y'],0)))
    right_elbow_angle = (find_angle((df['RIGHT_SHOULDER_x'],df['RIGHT_SHOULDER_y'],0),(df['RIGHT_ELBOW_x'], df['RIGHT_ELBOW_y'],0),(df['RIGHT_WRIST_x'],df['RIGHT_WRIST_y'],0)))
    left_elbow_angle = (find_angle((df['LEFT_WRIST_x'],df['LEFT_WRIST_y'],0),(df['LEFT_ELBOW_x'], df['LEFT_ELBOW_y'],0),(df['LEFT_SHOULDER_x'],df['LEFT_SHOULDER_y'],0)))
    left_knee_angle = standardize(find_angle((df['LEFT_HIP_x'],df['LEFT_HIP_y'],0),(df['LEFT_KNEE_x'], df['LEFT_KNEE_y'],0),(df['LEFT_ANKLE_x'],df['LEFT_ANKLE_y'],0)))
    
    print(left_hip_angle)
    print(right_knee_angle)
    print(left_knee_angle)
    print(right_elbow_angle)
    print(right_hip_angle)

    print(left_elbow_angle)
    

    if left_elbow_angle>61:
        command="Please raise your left wrist"
    elif left_elbow_angle<30:
        command="Please lower your left wrist"
    elif right_elbow_angle>60:
        command="Please raise your right wrist"
    elif right_elbow_angle<30:
        command="Please lower your right wrist"
    elif right_knee_angle>110:
        command="Please raise your right ankle"
    elif right_knee_angle<30:
        command="Please lower your right ankle"
    elif right_hip_angle<90:
        command="Please lower your right knee"
    elif right_hip_angle>145:
        command="Please raise your right knee"
    else:
        command="Correct Tree Pose"

    return command



def chair_pose_correction(df):

    command=""
    left_hip_angle = standardize(find_angle((df['LEFT_KNEE_x'],df['LEFT_KNEE_y'],0),(df['LEFT_HIP_x'], df['LEFT_HIP_y'],0),(df['LEFT_SHOULDER_x'],df['LEFT_SHOULDER_y'],0)))
    right_hip_angle = standardize(find_angle((df['RIGHT_KNEE_x'],df['RIGHT_KNEE_y'],0),(df['RIGHT_HIP_x'], df['RIGHT_HIP_y'],0),(df['RIGHT_SHOULDER_x'],df['RIGHT_SHOULDER_y'],0)))
    right_knee_angle = standardize(find_angle((df['RIGHT_HIP_x'],df['RIGHT_HIP_y'],0),(df['RIGHT_KNEE_x'], df['RIGHT_KNEE_y'],0),(df['RIGHT_ANKLE_x'],df['RIGHT_ANKLE_y'],0)))
    left_knee_angle = standardize(find_angle((df['LEFT_HIP_x'],df['LEFT_HIP_y'],0),(df['LEFT_KNEE_x'], df['LEFT_KNEE_y'],0),(df['LEFT_ANKLE_x'],df['LEFT_ANKLE_y'],0)))
    right_shoulder_angle = standardize(find_angle((df['RIGHT_ELBOW_x'],df['RIGHT_ELBOW_y'],0),(df['RIGHT_SHOULDER_x'], df['RIGHT_SHOULDER_y'],0),(df['RIGHT_HIP_x'],df['RIGHT_HIP_y'],0)))
    left_shoulder_angle = standardize(find_angle((df['LEFT_ELBOW_x'],df['LEFT_ELBOW_y'],0),(df['LEFT_SHOULDER_x'], df['LEFT_SHOULDER_y'],0),(df['LEFT_HIP_x'],df['LEFT_HIP_y'],0)))
    right_elbow_angle = standardize(find_angle((df['RIGHT_SHOULDER_x'],df['RIGHT_SHOULDER_y'],0),(df['RIGHT_ELBOW_x'], df['RIGHT_ELBOW_y'],0),(df['RIGHT_WRIST_x'],df['RIGHT_WRIST_y'],0)))
    left_elbow_angle = standardize(find_angle((df['LEFT_WRIST_x'],df['LEFT_WRIST_y'],0),(df['LEFT_ELBOW_x'], df['LEFT_ELBOW_y'],0),(df['LEFT_SHOULDER_x'],df['LEFT_SHOULDER_y'],0)))
    print(left_hip_angle)
    print(right_hip_angle)
    
    print(left_knee_angle)
    print(right_knee_angle)

    print(right_elbow_angle)

    print(left_elbow_angle)
    print(left_shoulder_angle)
    print(right_shoulder_angle)
    if right_knee_angle>125 or left_knee_angle>125:
        command = "Please bend your knees"
    elif right_knee_angle<90 or left_knee_angle<90:
        command = "Slightly raise your hip"
    elif right_hip_angle>130 or left_hip_angle>130:
        command="Lower your body forward"
    elif right_hip_angle<80 or left_hip_angle<80:
        command = "Raise your body backward"
    elif right_shoulder_angle>190 or left_shoulder_angle>190:
        command = "Lower and straighten your arms"
    elif left_shoulder_angle<150:
        command = "Raise and straighten your arms"
    elif left_elbow_angle<170 or right_elbow_angle>190 or left_elbow_angle>190:
        command = "Straighten elbows"
    else:
        command = "Chair pose correct!!"
    

    return command

def warrior_pose_correction(df):
    right_knee_angle = standardize(find_angle((df['RIGHT_HIP_x'],df['RIGHT_HIP_y'],0),(df['RIGHT_KNEE_x'], df['RIGHT_KNEE_y'],0),(df['RIGHT_ANKLE_x'],df['RIGHT_ANKLE_y'],0)))
    left_knee_angle = standardize(find_angle((df['LEFT_HIP_x'],df['LEFT_HIP_y'],0),(df['LEFT_KNEE_x'], df['LEFT_KNEE_y'],0),(df['LEFT_ANKLE_x'],df['LEFT_ANKLE_y'],0)))
    left_hip_angle = standardize(find_angle((df['LEFT_SHOULDER_x'],df['LEFT_SHOULDER_y'],0),(df['LEFT_HIP_x'], df['LEFT_HIP_y'],0),(df['LEFT_KNEE_x'],df['LEFT_KNEE_y'],0)))
    right_hip_angle = standardize(find_angle((df['RIGHT_KNEE_x'],df['RIGHT_KNEE_y'],0),(df['RIGHT_HIP_x'], df['RIGHT_HIP_y'],0),(df['RIGHT_SHOULDER_x'],df['RIGHT_SHOULDER_y'],0)))
    right_shoulder_angle = standardize(find_angle((df['RIGHT_ELBOW_x'],df['RIGHT_ELBOW_y'],0),(df['RIGHT_SHOULDER_x'], df['RIGHT_SHOULDER_y'],0),(df['RIGHT_HIP_x'],df['RIGHT_HIP_y'],0)))
    left_shoulder_angle = standardize(find_angle((df['LEFT_ELBOW_x'],df['LEFT_ELBOW_y'],0),(df['LEFT_SHOULDER_x'], df['LEFT_SHOULDER_y'],0),(df['LEFT_HIP_x'],df['LEFT_HIP_y'],0)))
    right_elbow_angle = standardize(find_angle((df['RIGHT_SHOULDER_x'],df['RIGHT_SHOULDER_y'],0),(df['RIGHT_ELBOW_x'], df['RIGHT_ELBOW_y'],0),(df['RIGHT_WRIST_x'],df['RIGHT_WRIST_y'],0)))
    left_elbow_angle = standardize(find_angle((df['LEFT_WRIST_x'],df['LEFT_WRIST_y'],0),(df['LEFT_ELBOW_x'], df['LEFT_ELBOW_y'],0),(df['LEFT_SHOULDER_x'],df['LEFT_SHOULDER_y'],0)))

    print(right_knee_angle)
    print(left_knee_angle)

    print(right_hip_angle)
    print(left_hip_angle)

    print(right_shoulder_angle)
    print(left_shoulder_angle)

    if right_hip_angle>110:
        command = "Lean your body forward"
    elif left_hip_angle<140:
        command = "Straighten your left leg"
    elif left_hip_angle>180:
        command = "Lower your left leg"
    elif right_hip_angle<55:
        command = "Straighten your right leg"
    elif left_knee_angle<150:
        command = "Straighten your left knee"
    elif right_knee_angle<150:
        command = "Straighten your right knee"
    elif right_shoulder_angle<160 or left_shoulder_angle<160:
        command = "Straighten your arms"
    elif right_elbow_angle<170 or left_elbow_angle<170 or right_elbow_angle>190 or left_elbow_angle>190:
        command = "Straighten elbows"
    else:
        command="Correct Warrior Pose!!"
    return command

# print(chair_pose_correction())
# if left_elbow_angle < 165:
#     print("Please straighten your left elbow") 
# if right_elbow_angle < 165:
#     print("Please straighten your right elbow") 
# if right_elbow_angle > 165 and right_elbow_angle < 180:
#     print("Please maintain the current position  in which both arms are straight") 
#     if left_shoulder_angle < 80:
#         print("Please raise your left armn such that the left arm is parallel to the ground") 
#     if left_shoulder_angle > 110:
#         print("Please lower your left armn such that the left arm is parallel to the ground") 
#     if right_shoulder_angle < 80:
#         print("Please raise your right armn such that the right arm is parallel to the ground") 
#     if right_shoulder_angle > 110:
#         print("Please lower your right armn such that the right arm is parallel to the ground") 
#         if left_shoulder_angle > 80 and left_shoulder_angle < 110 and right_shoulder_angle > 80 and right_shoulder_angle < 110:
#             print("Please maintain the current position  in which both arms are straight and are parallel to the ground")
#             if left_knee_angle < 165:
#                 print("Please straighten your left leg") 
#             if right_knee_angle < 90 or  right_knee_angle > 120:
#                 print("Please bend your right knee while maintaining the position") 
#                 if left_knee_angle > 165 and left_knee_angle < 195 and right_knee_angle > 90 and right_knee_angle < 120:
#                     print("The Warrior 11 pose is correct")
# print(tree_pose_correction())