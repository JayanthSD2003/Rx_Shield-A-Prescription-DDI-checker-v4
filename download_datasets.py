import kagglehub
import shutil
import os
import glob

# Define target directory
target_dir = os.path.join(os.getcwd(), "DDI_datasets and DB data", "Indian_Medicine_Database")
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

datasets = [
    "shudhanshusingh/az-medicine-dataset-of-india",
    "riturajsingh2004/extensive-a-z-medicines-dataset-of-india",
    "rishgeeky/indian-pharmaceutical-products",
    "apkaayush/india-medicines-and-drug-info-dataset",
    "ankushpoddar/all-india-drug-bank-database"
]

print(f"Target Directory: {target_dir}")

for dataset in datasets:
    try:
        print(f"\nDownloading {dataset}...")
        path = kagglehub.dataset_download(dataset)
        print(f"Downloaded to: {path}")
        
        # Move CSV files to target directory
        # Handle cases where the dataset might be in a subfolder or just files
        files = glob.glob(os.path.join(path, "**", "*.csv"), recursive=True)
        
        if not files:
             print(f"No CSV files found in {path}")
             continue
             
        for file in files:
            filename = os.path.basename(file)
            dest = os.path.join(target_dir, f"{dataset.replace('/', '_')}_{filename}")
            
            # Use unique names to avoid collisions if multiple datasets have same filenames
            if os.path.exists(dest):
                 print(f"File already exists: {dest}, skipping.")
            else:
                shutil.copy2(file, dest)
                print(f"Copied to: {dest}")
                
    except Exception as e:
        print(f"Error downloading {dataset}: {e}")

print("Download process completed.")
