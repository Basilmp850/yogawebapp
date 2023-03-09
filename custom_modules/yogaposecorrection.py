from math import degrees
from math import atan2

import pandas as pd

df = pd.read_csv('../static/image_csv/uploaded_image.csv')
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




print(find_angle((df['LEFT_SHOULDER_x'], df['LEFT_SHOULDER_y'], 0), (df['LEFT_ELBOW_x'], df['LEFT_ELBOW_y'], 0), (df['LEFT_WRIST_x'], df['LEFT_WRIST_y'], 0)))

    
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
# if left_elbow_angle < 165:
#     print("Please straighten your left elbow") 
# if right_elbow_angle < 165:
#     print("Please straighten your right elbow") 
# if right_elbow_angle > 165 and right_elbow_angle < 165:
#     print("Please maintain the current position  in which both arms are straight") 
#     if left_shoulder_angle < 80:
#         print("Please raise your left armn such that the left arm is parallel to the ground") 
#     if left_shoulder_angle > 110:
#         print("Please lower your left armn such that the left arm is parallel to the ground") 
#     if right_shoulder_angle < 80:
#         print("Please raise your right armn such that the left arm is parallel to the ground") 
#     if right_shoulder_angle > 110:
#         print("Please lower your right armn such that the left arm is parallel to the ground") 
#         if left_shoulder_angle > 80 and left_shoulder_angle < 110 and right_shoulder_angle > 80 and right_shoulder_angle < 110:
#             print("Please maintain the current position  in which both arms are straight and are parallel to the ground")
#             if left_knee_angle < 165:
#                 print("Please straighten your left leg") 
#             if right_knee_angle < 90 or  right_knee_angle > 120:
#                 print("Please bend your right knee while maintaining the position") 
#                 if left_knee_angle > 165 and left_knee_angle < 195 and right_knee_angle > 90 and right_knee_angle < 120:
#                     print("The Warrior 11 pose is correct")
