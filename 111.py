import matplotlib.pyplot as plt
import matplotlib.image as mpimg

img = mpimg.imread("passport_template2.jpg")

fig, ax = plt.subplots()
ax.imshow(img)

def onclick(event):
    print(f"X={int(event.xdata)}, Y={int(event.ydata)}")

cid = fig.canvas.mpl_connect('button_press_event', onclick)

plt.show()