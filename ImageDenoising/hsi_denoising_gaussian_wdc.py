import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import os
import argparse

from utility import *
from hsi_setup import Engine, train_options, make_dataset


if __name__ == '__main__':
    """Training settings"""
    parser = argparse.ArgumentParser(
        description='Hyperspectral Image Denoising (Complex noise)')
    opt = train_options(parser)
    print(opt)
    

    """Setup Engine"""
    engine = Engine(opt)

    """Dataset Setting"""
    HSI2Tensor = partial(HSI2Tensor, use_2dconv=engine.net.use_2dconv)

    target_transform = HSI2Tensor()

    train_transform = Compose([
        AddNoiseBlindv1(10,70),
        HSI2Tensor()
    ])

    wdc_64_31 = LMDBDataset(opt.training_dataset_path, repeat=10)
    
    
    target_transform = HSI2Tensor()
    train_dataset = ImageTransformDataset(wdc_64_31, train_transform,target_transform)
    print('==> Preparing data..')


    """Test-Dev"""
    basefolder = '/mnt/code/users/yuchunmiao/hypersigma-master/data/Hyperspectral_Project/WDC/test_noise/Patch_Cases/Case1'
    
    mat_datasets = [MatDataFromFolder(basefolder) ]

    # if not engine.get_net().use_2dconv:
    #     mat_transform = Compose([
    #         LoadMatHSI(input_key='input', gt_key='gt',
    #                 transform=lambda x:x[ ...][None], needsigma=False),
    #     ])
    # else:
    mat_transform = Compose([
        LoadMatHSI(input_key='input', gt_key='gt', needsigma=False),
    ])

    mat_datasets = [TransformDataset(mat_dataset, mat_transform)
                    for mat_dataset in mat_datasets]

    train_loader = DataLoader(train_dataset,
                              batch_size=opt.batchSize, shuffle=True,
                              num_workers=8, pin_memory=not opt.no_cuda, worker_init_fn=worker_init_fn)
    
    mat_loaders = [DataLoader(
        mat_dataset,
        batch_size=1, shuffle=False,
        num_workers=1, pin_memory=opt.no_cuda
    ) for mat_dataset in mat_datasets]        

    base_lr = opt.lr
    epoch_per_save = 10
    # adjust_learning_rate(engine.optimizer, opt.lr)

    # from epoch 50 to 100
    engine.epoch  = 0
    print("epoch is {} !!!".format(opt.epoch))
    while engine.epoch < opt.epoch:
        np.random.seed()

        # if engine.epoch == 15:
        #     adjust_learning_rate(engine.optimizer, base_lr*0.1)


        engine.validate(mat_loaders[0], 'wdc_eval')
        
        engine.train(train_loader,mat_loaders[0])

        
        adjust_learning_rate_new(engine.optimizer, engine.epoch, base_lr)
        
        display_learning_rate(engine.optimizer)
        print('Latest Result Saving...')
        model_latest_path = os.path.join(engine.basedir, engine.prefix, 'model_latest.pth')
        engine.save_checkpoint(
            model_out_path=model_latest_path
        )

        display_learning_rate(engine.optimizer)
        # if engine.epoch % epoch_per_save == 0:
        #     engine.save_checkpoint()
