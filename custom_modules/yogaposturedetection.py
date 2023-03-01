import tensorflow as tf
from sklearn.model_selection import train_test_split
from tensorflow import keras
import pandas as pd
import os
import sys
pose_sample_rpi_path = os.path.join(os.getcwd(), 'examples/lite/examples/pose_estimation/raspberry_pi')
sys.path.append(pose_sample_rpi_path)
import utils
from  data import BodyPart  
import tempfile
import csv
import tqdm
import numpy as np
from matplotlib import pyplot as plt
import cv2
import pickle 
from examples.lite.examples.pose_estimation.raspberry_pi.ml import Movenet

movenet = Movenet('movenet_thunder')
# BodyPart =  pickle.load(open('pickled_files/BodyPart.pkl', 'rb'))
# movenet = pickle.load(open('pickled_files/movenet.pkl','rb'))
# model = pickle.load(open('pickled_files/yogadetectionmodel.pkl','rb'))
model = tf.keras.models.load_model('pickled_files/my_model.h5')
class_names = pickle.load(open('pickled_files/class_names.pkl','rb'))



def detect(input_tensor, inference_count=3):
  """Runs detection on an input image.

  Args:
    input_tensor: A [height, width, 3] Tensor of type tf.float32.
      Note that height and width can be anything since the image will be
      immediately resized according to the needs of the model within this
      function.
    inference_count: Number of times the model should run repeatly on the
      same input image to improve detection accuracy.

  Returns:
    A Person entity detected by the MoveNet.SinglePose.
  """
  image_height, image_width, channel = input_tensor.shape

  # Detect pose using the full input image
  movenet.detect(input_tensor.numpy(), reset_crop_region=True)

  # Repeatedly using previous detection result to identify the region of
  # interest and only croping that region to improve detection accuracy
  for _ in range(inference_count - 1):
    person = movenet.detect(input_tensor.numpy(), 
                            reset_crop_region=False)

  return person

class MoveNetPreprocessor(object):
  """Helper class to preprocess pose sample images for classification."""

  def __init__(self,
               images_in_folder,
               images_out_folder,
               csvs_out_path):
    """Creates a preprocessor to detection pose from images and save as CSV.

    Args:
      images_in_folder: Path to the folder with the input images. It should
        follow this structure:
        yoga_poses
        |__ downdog
            |______ 00000128.jpg
            |______ 00000181.bmp
            |______ ...
        |__ goddess
            |______ 00000243.jpg
            |______ 00000306.jpg
            |______ ...
        ...
      images_out_folder: Path to write the images overlay with detected
        landmarks. These images are useful when you need to debug accuracy
        issues.
      csvs_out_path: Path to write the CSV containing the detected landmark
        coordinates and label of each image that can be used to train a pose
        classification model.
    """
    self._images_in_folder = images_in_folder
    self._images_out_folder = images_out_folder
    self._csvs_out_path = csvs_out_path
    self._messages = []

    # Create a temp dir to store the pose CSfVs per class
    self._csvs_out_folder_per_class = tempfile.mkdtemp()

    # Get list of pose classes and print image statistics
    self._pose_class_names = sorted(
        [n for n in os.listdir(self._images_in_folder) if not n.startswith('.')]
        )

  def process(self, per_pose_class_limit=None, detection_threshold=0.17):
    """Preprocesses images in the given folder.
    Args:
      per_pose_class_limit: Number of images to load. As preprocessing usually
        takes time, this parameter can be specified to make the reduce of the
        dataset for testing.
      detection_threshold: Only keep images with all landmark confidence score
        above this threshold.
    """
    # Loop through the classes and preprocess its images
    for pose_class_name in self._pose_class_names:
      print('Preprocessing', pose_class_name, file=sys.stderr)

      # Paths for the pose class.
      images_in_folder = os.path.join(self._images_in_folder, pose_class_name)
      images_out_folder = os.path.join(self._images_out_folder, pose_class_name)
      csv_out_path = os.path.join(self._csvs_out_folder_per_class,
                                  pose_class_name + '.csv')
      if not os.path.exists(images_out_folder):
        os.makedirs(images_out_folder)

      # Detect landmarks in each image and write it to a CSV file
      with open(csv_out_path, 'w') as csv_out_file:
        csv_out_writer = csv.writer(csv_out_file, 
                                    delimiter=',', 
                                    quoting=csv.QUOTE_MINIMAL)
        # Get list of images
        image_names = sorted(
            [n for n in os.listdir(images_in_folder) if not n.startswith('.')])
        if per_pose_class_limit is not None:
          image_names = image_names[:per_pose_class_limit]

        valid_image_count = 0

        # Detect pose landmarks from each image
        for image_name in image_names:
          image_path = os.path.join(images_in_folder, image_name)

          try:
            image = tf.io.read_file(image_path)
            image = tf.io.decode_jpeg(image)
          except:
            self._messages.append('Skipped ' + image_path + '. Invalid image.')
            continue
          else:
            image = tf.io.read_file(image_path)
            image = tf.io.decode_jpeg(image)
            image_height, image_width, channel = image.shape

          # Skip images that isn't RGB because Movenet requires RGB images
          if channel != 3:
            self._messages.append('Skipped ' + image_path +
                                  '. Image isn\'t in RGB format.')
            continue
          person = detect(image)

          # Save landmarks if all landmarks were detected
          min_landmark_score = min(
              [keypoint.score for keypoint in person.keypoints])
          should_keep_image = min_landmark_score >= detection_threshold
          if not should_keep_image:
            self._messages.append('Skipped ' + image_path +
                                  '. No pose was confidentlly detected.')
            continue

          valid_image_count += 1

          # Draw the prediction result on top of the image for debugging later
          # output_overlay = draw_prediction_on_image(
          #     image.numpy().astype(np.uint8), person, 
          #     close_figure=True, keep_input_size=True)

          # # Write detection result into an image file
          # output_frame = cv2.cvtColor(output_overlay, cv2.COLOR_RGB2BGR)
          # cv2.imwrite(os.path.join(images_out_folder, image_name), output_frame)

          # Get landmarks and scale it to the same size as the input image
          pose_landmarks = np.array(
              [[keypoint.coordinate.x, keypoint.coordinate.y, keypoint.score]
                for keypoint in person.keypoints],
              dtype=np.float32)

          # Write the landmark coordinates to its per-class CSV file
          coordinates = pose_landmarks.flatten().astype(np.str_).tolist()
          csv_out_writer.writerow([image_name] + coordinates)

        if not valid_image_count:
          print("No valid poses found!!")
          # raise RuntimeError(
          #     'No valid images found for the "{}" class.'
          #     .format(pose_class_name))

    # Print the error message collected during preprocessing.
    # print('\n'.join(self._messages))

    # Combine all per-class CSVs into a single output file
    if valid_image_count:
     all_landmarks_df = self._all_landmarks_as_dataframe()
     all_landmarks_df.to_csv(self._csvs_out_path, index=False)

  def class_names(self):
    """List of classes found in the training dataset."""
    return self._pose_class_names

  def _all_landmarks_as_dataframe(self):
    """Merge all per-class CSVs into a single dataframe."""
    total_df = None
    for class_index, class_name in enumerate(self._pose_class_names):
      csv_out_path = os.path.join(self._csvs_out_folder_per_class,
                                  class_name + '.csv')
      per_class_df = pd.read_csv(csv_out_path, header=None)

      # Add the labels
      per_class_df['class_no'] = [class_index]*len(per_class_df)
      per_class_df['class_name'] = [class_name]*len(per_class_df)

      # Append the folder name to the filename column (first column)
      per_class_df[per_class_df.columns[0]] = (os.path.join(class_name, '') 
        + per_class_df[per_class_df.columns[0]].astype(str))

      if total_df is None:
        # For the first class, assign its data to the total dataframe
        total_df = per_class_df
      else:
        # Concatenate each class's data into the total dataframe
        total_df = pd.concat([total_df, per_class_df], axis=0)

    list_name = [[bodypart.name + '_x', bodypart.name + '_y', 
                  bodypart.name + '_score'] for bodypart in BodyPart] 
    header_name = []
    for columns_name in list_name:
      header_name += columns_name
    header_name = ['file_name'] + header_name
    header_map = {total_df.columns[i]: header_name[i] 
                  for i in range(len(header_name))}

    total_df.rename(header_map, axis=1, inplace=True)

    return total_df


# def draw_prediction_on_image(
#     image, person, crop_region=None, close_figure=True,
#     keep_input_size=False):
#   """Draws the keypoint predictions on image.

#   Args:
#     image: An numpy array with shape [height, width, channel] representing the
#       pixel values of the input image.
#     person: A person entity returned from the MoveNet.SinglePose model.
#     close_figure: Whether to close the plt figure after the function returns.
#     keep_input_size: Whether to keep the size of the input image.

#   Returns:
#     An numpy array with shape [out_height, out_width, channel] representing the
#     image overlaid with keypoint predictions.
#   """
#   # Draw the detection result on top of the image.
#   image_np = utils.visualize(image, [person])

#   # Plot the image with detection results.
#   height, width, channel = image.shape
#   aspect_ratio = float(width) / height
#   fig, ax = plt.subplots(figsize=(12 * aspect_ratio, 12))
#   im = ax.imshow(image_np)

#   if close_figure:
#     plt.close(fig)

#   if not keep_input_size:
#     image_np = utils.keep_aspect_ratio_resizer(image_np, (512, 512))

#   return image_np


csvs_out_test_path = 'static/image_csv/uploaded_image.csv'
# IMAGES_ROOT = "static"
# images_in_test_folder = os.path.join(IMAGES_ROOT, 'uploadedimage')
# images_out_test_folder = 'uploadedimage_output'
# csvs_out_test_path = 'uploaded_image.csv'

# preprocessor = MoveNetPreprocessor(
#       images_in_folder=images_in_test_folder,
#       images_out_folder=images_out_test_folder,
#       csvs_out_path=csvs_out_test_path,
#   )

# preprocessor.process(per_pose_class_limit=None)

def load_pose_landmarks(csv_path):
  """Loads a CSV created by MoveNetPreprocessor.

  Returns:
    X: Detected landmark coordinates and scores of shape (N, 17 * 3)
    y: Ground truth labels of shape (N, label_count)
    classes: The list of all class names found in the dataset
    dataframe: The CSV loaded as a Pandas dataframe features (X) and ground
      truth labels (y) to use later to train a pose classification model.
  """

  # Load the CSV file
  dataframe = pd.read_csv(csv_path)
  df_to_process = dataframe.copy()

  # Drop the file_name columns as you don't need it during training.
  df_to_process.drop(columns=['file_name'], inplace=True)

  # Extract the list of class names
  classes = df_to_process.pop('class_name').unique()

  # Extract the labels
  y = df_to_process.pop('class_no')

  # Convert the input features and labels into the correct format for training.
  X = df_to_process.astype('float64')
  y = keras.utils.to_categorical(y)

  return X, y, classes, dataframe
# X, y, class_names, _ = load_pose_landmarks(csvs_out_train_path)

# Split training data (X, y) into (X_train, y_train) and (X_val, y_val)
# X_train, X_val, y_train, y_val = train_test_split(X, y,
                                                  # test_size=0.15)
if len(os.listdir('static/image_csv'))!=0:
 X_test, y_test, _, df_test = load_pose_landmarks(csvs_out_test_path)
def get_center_point(landmarks, left_bodypart, right_bodypart):
  """Calculates the center point of the two given landmarks."""

  left = tf.gather(landmarks, left_bodypart.value, axis=1)
  right = tf.gather(landmarks, right_bodypart.value, axis=1)
  center = left * 0.5 + right * 0.5
  return center


def get_pose_size(landmarks, torso_size_multiplier=2.5):
  """Calculates pose size.

  It is the maximum of two values:
    * Torso size multiplied by `torso_size_multiplier`
    * Maximum distance from pose center to any pose landmark
  """
  # Hips center
  hips_center = get_center_point(landmarks, BodyPart.LEFT_HIP, 
                                 BodyPart.RIGHT_HIP)

  # Shoulders center
  shoulders_center = get_center_point(landmarks, BodyPart.LEFT_SHOULDER,
                                      BodyPart.RIGHT_SHOULDER)

  # Torso size as the minimum body size
  torso_size = tf.linalg.norm(shoulders_center - hips_center)

  # Pose center
  pose_center_new = get_center_point(landmarks, BodyPart.LEFT_HIP, 
                                     BodyPart.RIGHT_HIP)
  pose_center_new = tf.expand_dims(pose_center_new, axis=1)
  # Broadcast the pose center to the same size as the landmark vector to
  # perform substraction
  pose_center_new = tf.broadcast_to(pose_center_new,
                                    [tf.size(landmarks) // (17*2), 17, 2])

  # Dist to pose center
  d = tf.gather(landmarks - pose_center_new, 0, axis=0,
                name="dist_to_pose_center")
  # Max dist to pose center
  max_dist = tf.reduce_max(tf.linalg.norm(d, axis=0))

  # Normalize scale
  pose_size = tf.maximum(torso_size * torso_size_multiplier, max_dist)

  return pose_size


# def normalize_pose_landmarks(landmarks):
#   """Normalizes the landmarks translation by moving the pose center to (0,0) and
#   scaling it to a constant pose size.
#   """
#   # Move landmarks so that the pose center becomes (0,0)
#   pose_center = get_center_point(landmarks, BodyPart.LEFT_HIP, 
#                                  BodyPart.RIGHT_HIP)
#   pose_center = tf.expand_dims(pose_center, axis=1)
#   # Broadcast the pose center to the same size as the landmark vector to perform
#   # substraction
#   pose_center = tf.broadcast_to(pose_center, 
#                                 [tf.size(landmarks) // (17*2), 17, 2])
#   landmarks = landmarks - pose_center

#   # Scale the landmarks to a constant pose size
#   pose_size = get_pose_size(landmarks)
#   landmarks /= pose_size

#   return landmarks


# def landmarks_to_embedding(landmarks_and_scores):
#   """Converts the input landmarks into a pose embedding."""
#   # Reshape the flat input into a matrix with shape=(17, 3)
#   reshaped_inputs = keras.layers.Reshape((17, 3))(landmarks_and_scores)

#   # Normalize landmarks 2D
#   landmarks = normalize_pose_landmarks(reshaped_inputs[:, :, :2])

#   # Flatten the normalized landmark coordinates into a vector
#   embedding = keras.layers.Flatten()(landmarks)

#   return embedding

# Add a checkpoint callback to store the checkpoint that has the highest
# validation accuracy.
checkpoint_path = "weights.best.hdf5"
checkpoint = keras.callbacks.ModelCheckpoint(checkpoint_path,
                             monitor='val_accuracy',
                             verbose=1,
                             save_best_only=True,
                             mode='max')
earlystopping = keras.callbacks.EarlyStopping(monitor='val_accuracy', 
                                              patience=20)

# Start training

# Classify pose in the TEST dataset using the trained model
if len(os.listdir('static/image_csv'))!=0:
 y_pred = model.predict(X_test)

# Convert the prediction result to class name
 y_pred_label = [class_names[i] for i in np.argmax(y_pred, axis=1)]
# y_true_label = [class_names[i] for i in np.argmax(y_test, axis=1)]

# print(y_pred_label[0])