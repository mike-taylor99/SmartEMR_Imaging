import os
import torch
from monai.networks.nets import densenet121
from monai.transforms import (
    AddChannel,
    Compose,
    LoadImage,
    ScaleIntensity,
    ToTensor,
)

from SmartEMR_Imaging.utils.makeModel import MedNISTDataset
from PIL import Image

# define labels and tags array(s)
class_names = ['AbdomenCT', 'BreastMRI', 'CXR', 'ChestCT', 'Hand', 'HeadCT']
class_tags = [['Abdomen CT Scan', 'CT Scan', 'Abdomen', 'CAT Scan', 'CT', 'CAT', 'Scan', 'Tomography', 'Abdominal'],
                    ['Breast MRI', 'Breast', 'MRI', 'Magnetic Resonance Imaging', 'Upper Ventral'], 
                    ['Chest X-Ray', 'Chest', 'X-Ray'], 
                    ['Chest CT Scan', 'CT Scan', 'Chest', 'CAT Scan', 'CT', 'CAT', 'Scan', 'Tomography'], 
                    ['Hand X-Ray', 'Hand', 'X-Ray'], 
                    ['Head CT Scan', 'Head', 'Brain', 'Brain Scan', 'CT Scan', 'CAT Scan', 'CT', 'CAT', 'Scan', 'Tomography']]
num_class = len(class_names)

def classify_image(image):
    # make conversions to image and save temporarily
    im = Image.open(image)
    im = im.convert(mode='L')
    im = im.resize((64, 64))
    im.save('conversion.jpeg', 'JPEG')

    # Define MONAI transforms, Dataset and Dataloader to process image
    val_transforms = Compose([LoadImage(image_only=True), AddChannel(), ScaleIntensity(), ToTensor()])
    test_ds = MedNISTDataset(['conversion.jpeg'], [0], val_transforms)
    test_loader = torch.utils.data.DataLoader(test_ds)

    # Define Network
    device = torch.device("cpu")
    model = densenet121(spatial_dims=2, in_channels=1, out_channels=num_class).to(device)

    # Make prediction
    model.load_state_dict(torch.load("SmartEMR_Imaging/MONAI_DATA_DIRECTORY/best_metric_model_cpu.pth"))
    model.eval()
    y_true = list()
    y_pred = list()
    with torch.no_grad():
        for test_data in test_loader:
            test_images, test_labels = (
                test_data[0].to(device),
                test_data[1].to(device),
                )
            pred = model(test_images).argmax(dim=1)
            for i in range(len(pred)):
                y_true.append(test_labels[i].item())
                y_pred.append(pred[i].item())

    # clean up
    os.remove('conversion.jpeg')

    return class_tags[y_pred[0]]
