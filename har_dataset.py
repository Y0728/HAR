from torch.utils.data import Dataset, DataLoader
import numpy as np
import pandas as pd
from numpy import genfromtxt


class MyDataSet(Dataset):

    def __init__(self, path, type, act_list):
        """可以在初始化函数当中对数据进行一些操作，比如读取、归一化等"""
        # self.data = np.loadtxt(path)  # 读取 txt 数据
        # self.x = self.data[:, 1:]  # 输入变量
        # self.y = self.data[:, 0]  # 输出变量
        self.act_dir = {'none': 0, 'walk': 1, 'run': 2, 'sit': 3, 'fall': 4}
        self.activity_list = act_list  # ['walk','run','sit','run','stand','none']
        self.datapath = path  # '/har_data/'
        # self.type = type # 'target' or 'point'

        if type == 'target':
            self.x, self.y = createTargetDataset(self.path, self.activity_list)
        elif type == 'point':
            self.x, self.y = createPointDataset(self.path, self.activity_list)
        else:
            print('The type of dataset is not supported!')
            sys.exit(1)

    def check_exists(self, path):
        return os.path.exists(path)

    def createTargetDataset(self, path, activity_list):
        x = []
        for activity in activity_list:
            data = []
            a_path = os.path.join(self.datapath, activity)

            if not self.check_exists(a_path):
                raise RuntimeError('Dataset not found.')

            for root, dirs, _ in os.walk(a_path):
                raw_path = os.path.join(root, dirs, 'raw/*point.csv')
                raw_data_files = glob.glob(raw_path)

                for file in raw_data_files:
                    data = genfromtxt(file, delimiter=',')[:, 2:11]  # pos_x, pos_y, pos_z, vx, vy, vz, ax, ay, az
                    x = data.append(data)

            if data.size == 0:
                print('Warning: The raw data of ' + activity + ' is not found!')
            else:
                y = y.append(np.ones((len(x), 1)) * self.act_dir[activity])

        if x.size == 0:
            print('Error: Dataset is not found.')
            sys.exit(1)
        return x, y

    def createPointDataset(self, path, activity_list):
        pass

    def __len__(self):
        """返回数据集当中的样本个数"""
        return len(self.x)

    def __getitem__(self, index):
        """返回样本集中的第 index 个样本；输入变量在前，输出变量在后"""
        return self.x[index, :], self.y[index]


data_set = MyDataSet('data.txt')
data_loader = DataLoader(dataset=data_set, batch_size=400, shuffle=True, drop_last=False)
