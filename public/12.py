import torch
from transformers import DPTForDepthEstimation, DPTImageProcessor
import numpy as np
import open3d as o3d
from PIL import Image
import cv2

# Load DPT model and feature extractor
model = DPTForDepthEstimation.from_pretrained("Intel/dpt-large")
feature_extractor = DPTImageProcessor.from_pretrained("Intel/dpt-large")

# Load and preprocess image
image_path = r"C:\Kmit\Project\my-app\public\1.ico.png"
image = Image.open(image_path).convert("RGB")
image_np = np.array(image)

# Convert to grayscale and apply Gaussian Blur
gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)

# Apply edge detection
edges = cv2.Canny(blurred, 50, 150)

# Dilate edges to make them more pronounced
dilated_edges = cv2.dilate(edges, np.ones((5, 5), np.uint8), iterations=2)

# Find contours
contours, _ = cv2.findContours(dilated_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Create mask for the detected objects
object_mask = np.zeros_like(edges)
cv2.drawContours(object_mask, contours, -1, (255), thickness=cv2.FILLED)

# Apply the mask to the original image to isolate objects
isolated_objects = cv2.bitwise_and(image_np, image_np, mask=object_mask)
isolated_objects[object_mask == 0] = [0, 0, 0]  # Black-out background

# Convert isolated objects to PIL format for depth estimation
isolated_objects_pil = Image.fromarray(isolated_objects)

# Preprocess image for depth estimation
inputs = feature_extractor(images=isolated_objects_pil, return_tensors="pt")

# Perform inference for depth estimation
with torch.no_grad():
    outputs = model(**inputs)
    depth_map = outputs.predicted_depth.squeeze().cpu().numpy()

# Normalize the depth map
depth_map = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min())

# Generate 3D point cloud from depth map, excluding background
h, w = depth_map.shape
x = np.linspace(0, w, w)
y = np.linspace(0, h, h)
X, Y = np.meshgrid(x, y)
Z = depth_map

# Flatten and filter points with valid object depth
points = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)

# Resize the object_mask to match depth map dimensions
object_mask_resized = cv2.resize(object_mask, (w, h), interpolation=cv2.INTER_NEAREST)
mask = (object_mask_resized > 0).ravel()  # Apply mask to filter valid points

# Filter points and colors
points = points[mask]

# Get RGB values from the isolated objects image
rgb = np.array(isolated_objects_pil.resize((w, h))) / 255.0  # Normalize to [0, 1]
colors = rgb.reshape(-1, 3)[mask]  # Apply the mask to colors

# Create the point cloud
pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(points)
pcd.colors = o3d.utility.Vector3dVector(colors)

# Estimate normals for better visualization
pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.01, max_nn=30))

# Create a mesh from the point cloud using Ball Pivoting Algorithm
radii = [0.005, 0.01, 0.02, 0.04]
mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
    pcd, o3d.utility.DoubleVector(radii)
)

# Smooth the mesh to improve appearance
mesh = mesh.filter_smooth_simple(number_of_iterations=5)
mesh.compute_vertex_normals()

# Apply the colors from the point cloud to the mesh vertices
mesh.vertex_colors = pcd.colors

# Visualize the mesh with better lighting
vis = o3d.visualization.Visualizer()
vis.create_window()
vis.add_geometry(mesh)

opt = vis.get_render_option()
opt.light_on = True
opt.background_color = np.array([0, 0, 0])  # Set background color to black for better contrast

# Adjust view settings
ctr = vis.get_view_control()
ctr.set_front([0.0, 0.0, -1.0])
ctr.set_up([0.0, -1.0, 0.0])
ctr.set_lookat([0.0, 0.0, 0.0])
ctr.set_zoom(0.8)

# Function to capture and save viewpoints
def capture_viewpoint(view_control, filename):
    # Capture and save the current view
    vis.capture_screen_image(filename)

# Capture different viewpoints
viewpoints = [
    {"front": [0.0, 0.0, -1.0], "filename": "view_front.png"},
    {"front": [1.0, 0.0, 0.0], "filename": "view_side.png"},
    {"front": [0.0, 1.0, 0.0], "filename": "view_top.png"}
]

for vp in viewpoints:
    ctr.set_front(vp["front"])
    vis.poll_events()
    vis.update_renderer()
    capture_viewpoint(ctr, vp["filename"])

# Run the visualization
vis.run()
vis.destroy_window()

# Save the 3D model with color
o3d.io.write_triangle_mesh("3d_model_no_bg_with_color.ply", mesh)
