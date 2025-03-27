import numpy as np
import requests
import matplotlib.pyplot as plt
from skimage.util.dtype import convert
from skimage import io
from skimage.transform import resize
from scipy.interpolate import CubicSpline      # for warping
from transforms3d.axangles import axangle2mat  # for rotation


def read_image_url(url):
    """Read an image from a URL using skimage.
    
    Args:
        url (str): URL of the file.
    
    Returns:
        np.array: An image.
    
    Examples:
        >>> img = read_image_url('https://raw.githubusercontent.com/miguelgfierro/codebase/master/share/Lenna.png')
        >>> img.shape
        (512, 512, 3)
    """
    return io.imread(url)


def resize_image(img, new_width, new_height):
    """Resize image to a ``new_width`` and ``new_height``.
    
    Args:
        img (np.array): An image.
        new_width (int): New width.
        new_height (int): New height.
    
    Returns:
        np.array: A resized image.
    
    Examples:
        >>> img = Image.open('share/Lenna.png')
        >>> img_resized = resize_image(img, 256, 256)
        >>> img_resized.shape
        (256, 256, 3)
    """
    img_new = resize(img, (int(new_width), int(new_height)), anti_aliasing=True)
    return convert(img_new, dtype=img.dtype)


def plot_image(img):
    """Plot an image.
    
    Args:
        img (np.array): An image.
    
    **Examples**::
    
        >> img = io.imread('share/Lenna.png')
        >> plot_image(img)
    """
    io.imshow(img)
    plt.axis("off")
    plt.show()
    
    
def show_file(filename):
    with open(filename, "r") as f:
        print(f.read())
        
    
def plot_series(x, title=None, xx=None, title_xx=None, axis=[0,3600,-1.5,1.5], linewidth=0.5):
    if xx is None:
        plt.plot(x, linewidth=linewidth)
        plt.title(title)
        plt.axis(axis)
    else:
        plt.figure(figsize=(15,4))
        plt.subplot(121)
        plt.plot(x, linewidth=linewidth)
        plt.title(title)
        plt.axis(axis)
        plt.subplot(122)
        plt.plot(xx, linewidth=linewidth)
        plt.title(title_xx)
        plt.axis(axis)
    plt.show()
    

# Original source: https://github.com/terryum/Data-Augmentation-For-Wearable-Sensor-Data
def DA_Jitter(X, sigma=0.05):
    myNoise = np.random.normal(loc=0, scale=sigma, size=X.shape)
    return X+myNoise


def DA_Scaling(X, sigma=0.1):
    scalingFactor = np.random.normal(loc=1.0, scale=sigma, size=(1,X.shape[1])) # shape=(1,3)
    myNoise = np.matmul(np.ones((X.shape[0],1)), scalingFactor)
    return X*myNoise


def GenerateRandomCurves(X, sigma=0.2, knot=4):
    """
    This example using cubic splice is not the best approach to generate random curves. 
    You can use other aprroaches, e.g., Gaussian process regression, Bezier curve, etc.
    """
    xx = (np.ones((X.shape[1],1))*(np.arange(0,X.shape[0], (X.shape[0]-1)/(knot+1)))).transpose()
    yy = np.random.normal(loc=1.0, scale=sigma, size=(knot+2, X.shape[1]))
    x_range = np.arange(X.shape[0])
    cs_x = CubicSpline(xx[:,0], yy[:,0])
    cs_y = CubicSpline(xx[:,1], yy[:,1])
    cs_z = CubicSpline(xx[:,2], yy[:,2])
    return np.array([cs_x(x_range),cs_y(x_range),cs_z(x_range)]).transpose()


def DA_MagWarp(X, sigma, knot):
    return X * GenerateRandomCurves(X, sigma, knot)


def DistortTimesteps(X, sigma, knot):
    tt = GenerateRandomCurves(X, sigma, knot) # Regard these samples aroun 1 as time intervals
    tt_cum = np.cumsum(tt, axis=0)        # Add intervals to make a cumulative graph
    # Make the last value to have X.shape[0]
    t_scale = [(X.shape[0]-1)/tt_cum[-1,0],(X.shape[0]-1)/tt_cum[-1,1],(X.shape[0]-1)/tt_cum[-1,2]]
    tt_cum[:,0] = tt_cum[:,0]*t_scale[0]
    tt_cum[:,1] = tt_cum[:,1]*t_scale[1]
    tt_cum[:,2] = tt_cum[:,2]*t_scale[2]
    return tt_cum


def DA_TimeWarp(X, sigma, knot):
    tt_new = DistortTimesteps(X, sigma, knot)
    X_new = np.zeros(X.shape)
    x_range = np.arange(X.shape[0])
    X_new[:,0] = np.interp(x_range, tt_new[:,0], X[:,0])
    X_new[:,1] = np.interp(x_range, tt_new[:,1], X[:,1])
    X_new[:,2] = np.interp(x_range, tt_new[:,2], X[:,2])
    return X_new


def DA_Rotation(X):
    axis = np.random.uniform(low=-1, high=1, size=X.shape[1])
    angle = np.random.uniform(low=-np.pi, high=np.pi)
    return np.matmul(X , axangle2mat(axis,angle))


def DA_Permutation(X, nPerm=4, minSegLength=10):
    X_new = np.zeros(X.shape)
    idx = np.random.permutation(nPerm)
    bWhile = True
    while bWhile == True:
        segs = np.zeros(nPerm+1, dtype=int)
        segs[1:-1] = np.sort(np.random.randint(minSegLength, X.shape[0]-minSegLength, nPerm-1))
        segs[-1] = X.shape[0]
        if np.min(segs[1:]-segs[0:-1]) > minSegLength:
            bWhile = False
    pp = 0
    for ii in range(nPerm):
        x_temp = X[segs[idx[ii]]:segs[idx[ii]+1],:]
        X_new[pp:pp+len(x_temp),:] = x_temp
        pp += len(x_temp)
    return X_new


def RandSampleTimesteps(X, nSample=1000):
    X_new = np.zeros(X.shape)
    tt = np.zeros((nSample,X.shape[1]), dtype=int)
    tt[1:-1,0] = np.sort(np.random.randint(1,X.shape[0]-1,nSample-2))
    tt[1:-1,1] = np.sort(np.random.randint(1,X.shape[0]-1,nSample-2))
    tt[1:-1,2] = np.sort(np.random.randint(1,X.shape[0]-1,nSample-2))
    tt[-1,:] = X.shape[0]-1
    return tt


def DA_RandSampling(X, nSample=1000):
    tt = RandSampleTimesteps(X, nSample)
    X_new = np.zeros(X.shape)
    X_new[:,0] = np.interp(np.arange(X.shape[0]), tt[:,0], X[tt[:,0],0])
    X_new[:,1] = np.interp(np.arange(X.shape[0]), tt[:,1], X[tt[:,1],1])
    X_new[:,2] = np.interp(np.arange(X.shape[0]), tt[:,2], X[tt[:,2],2])
    return X_new


