from statemachine import StateMachine, State
import pandas as pd
import math

target_cols = ['frame_id', 'target_id', 'pos_x', 'pos_y', 'pos_z', 'vx', 'vy', 'vz', 'ax', 'ay', 'az', 'xoy_delta']


class StateDetectionMachine(StateMachine):

    def __init__(self):
        super(StateDetectionMachine, self).__init__()
        self.data = pd.DataFrame(columns=target_cols)
        self.copy_data = None
        self.stand2fall_posz_threshold = 0.65
        self.fall2stand_posz_threshold = 1.4
        self.fall2stand_cnt = 0
        self.stand2fall_cnt = 0

        self.stand2sit_posz_threshold = 1.05
        self.sit2stand_posz_threshold = 1.4
        self.sit2stand_cnt = 0
        self.stand2sit_cnt = 0

        self.sit2fall_cnt = 0

        self.cnt_call_stand2sit = 0

        self.window_size = 10
        self.ave_size = self.window_size - 5

        self.stand2sit_flag = 0

    def insert_data(self, line):
        # print(line[1], ":", "pos_z", line[4])
        self.data = self.data.append(line).reset_index(drop=True)
        if len(self.data) > self.window_size:
            x1 = self.data.iloc[self.window_size]['pos_x']
            x2 = self.data.iloc[1]['pos_x']
            y1 = self.data.iloc[self.window_size]['pos_y']
            y2 = self.data.iloc[1]['pos_y']
            xoy_delta = math.sqrt((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2))
            self.data.at[self.window_size, "xoy_delta"] = xoy_delta
            self.data = self.data.drop([0])
        self.copy_data = self.data.copy()
        self.copy_data['posz_1'] = self.copy_data["pos_z"].shift(-1) - self.copy_data["pos_z"]
        self.copy_data['xoy_delta_1'] = self.copy_data["xoy_delta"].shift(-1) - self.copy_data["xoy_delta"]

    # 状态定义
    stand = State("stand", initial=True)
    walk = State("walk")
    fall = State("fall")
    sit = State("sit")
    run = State("run")

    # 状态转换
    stand2walk = stand.to(walk)
    stand2run = stand.to(run)
    stand2sit = stand.to(sit)
    stand2fall = stand.to(fall)

    walk2run = walk.to(run)
    walk2sit = walk.to(sit)
    walk2fall = walk.to(fall)
    walk2stand = walk.to(stand)

    run2stand = run.to(stand)
    run2sit = run.to(sit)
    run2fall = run.to(fall)
    run2walk = run.to(walk)

    fall2stand = fall.to(stand)
    fall2walk = fall.to(walk)
    fall2run = fall.to(run)

    sit2stand = sit.to(stand)
    sit2walk = sit.to(walk)
    sit2run = sit.to(run)
    sit2fall = sit.to(fall)

    def check_stand2fall(self):
        cnt_vz_less_threshold = len(self.data[(self.data['vz'] <= 0)].index.tolist())
        cnt_height_less_threshold = len(self.data[(self.data['pos_z'] < self.stand2fall_posz_threshold)].index.tolist())
        cnt_cz_less_threashold = len(self.copy_data[(self.copy_data['posz_1'] <= 0)].index.tolist())
        cnt_cxoy_great_threshold = len(self.copy_data[(self.copy_data['xoy_delta_1'] <= 0)].index.tolist())
        
        # ave_height = self.data.iloc[self.ave_size:self.window_size]['pos_z'].mean()
        cnt_xoy_delta_great_threshold = len(self.copy_data[(self.copy_data['xoy_delta'] >= 0.5)].index.tolist())
        if cnt_height_less_threshold > 7 and (cnt_cz_less_threashold > 4 or cnt_vz_less_threshold > 3) \
                and cnt_xoy_delta_great_threshold > 3 and cnt_cxoy_great_threshold > 3:
            # self.stand2sit_flag = 0
            return True
        else:
            return False

    def check_fall2stand(self):
        cnt_vz_greater_threshold = len(self.data[(self.data['vz'] >= 0)].index.tolist())
        cnt_height_greater_threshold = len(
            self.data[(self.data['pos_z'] > self.fall2stand_posz_threshold)].index.tolist())
        cnt_fall2stand_not_detection = len(self.data[(self.data['pos_z'] > self.fall2stand_posz_threshold)].index.tolist())
        if (cnt_vz_greater_threshold > 4 and cnt_height_greater_threshold > 3) or cnt_fall2stand_not_detection > 6:
            return True
        else:
            return False

    def check_stand2sit(self):
        # if self.stand2sit_flag != 0:
        #     self.stand2sit_flag += 1
        #     if self.stand2sit_flag < 3:
        #         return False
        #     else:
        #         self.stand2sit_flag = 0
        #         cnt_cz_less_threshold = len(self.copy_data[(self.copy_data['posz_1'] <= 0)]
        #                                     .iloc[self.ave_size:self.window_size].index.tolist())
        #         if cnt_cz_less_threshold > 3:
        #             return False
        #         else:
        #             return True
        # else:
        cnt_vz_less_threshold = len(self.data[(self.data['vz'] <= 0)].index.tolist())
        cnt_height_less_threshold = len(
            self.data[(self.data['pos_z'] < self.stand2sit_posz_threshold)].index.tolist())
        cnt_cz_less_threshold = len(self.copy_data[(self.copy_data['posz_1'] <= 0)].index.tolist())
        cnt_cxoy_less_threshold = len(self.copy_data[(self.copy_data['xoy_delta_1'] <= 0)].index.tolist())
        # ave_height = self.data.iloc[self.ave_size:self.window_size]['pos_z'].mean()
        cnt_xoy_delta_less_threshold = len(self.data[(self.data['xoy_delta'] <= 0.33)].index.tolist())
        if cnt_height_less_threshold > 5 and (cnt_cz_less_threshold > 5 or cnt_vz_less_threshold > 3) \
                and cnt_xoy_delta_less_threshold > 3 and cnt_cxoy_less_threshold > 5:
            # self.stand2sit_flag = 1
            return True
        else:
            return False

    def check_sit2stand(self):
        cnt_vz_greater_threshold = len(self.data[(self.data['vz'] >= 0)].index.tolist())
        cnt_height_greater_threshold = len(
            self.data[(self.data['pos_z'] > self.sit2stand_posz_threshold)].index.tolist())
        cnt_sit2stand_not_detection = len(self.data[(self.data['pos_z'] > self.sit2stand_posz_threshold)].index.tolist())
        if (cnt_vz_greater_threshold > 4 and cnt_height_greater_threshold > 3) or cnt_sit2stand_not_detection > 6:
            return True
        else:
            return False

    def check_sit2fall(self):
        cnt_height_less_threshod = len(self.data[(self.data['pos_z'] < self.stand2fall_posz_threshold)].index.tolist())
        if cnt_height_less_threshod > 6:
            return True
        else:
            return False

    def check_stand2walk(self):
        cnt_xoy_delta_greater_threshold = len(self.data[(self.data['xoy_delta'] >= 0.4)].index.tolist())
        if cnt_xoy_delta_greater_threshold > 5:
            return True
        return False


    def check_walk2stand(self):
        cnt_xoy_delta_less_threshold = len(self.data[(self.data['xoy_delta'] <= 0.1)].index.tolist())
        if cnt_xoy_delta_less_threshold > 5:
            return True
        return False

    def on_sit2fall(self):
        self.sit2fall_cnt += 1
        print("sit -> fall triggered")

    def on_stand2fall(self):
        self.stand2fall_cnt += 1
        print("stand -> fall triggered!")

    def on_fall2stand(self):
        self.fall2stand_cnt += 1
        print("fall -> stand triggered!")

    def on_stand2sit(self):
        self.stand2sit_cnt += 1
        print("stand -> sit triggered!")

    def on_sit2stand(self):
        self.sit2stand_cnt += 1
        print("sit -> stand triggered!")

    def process(self, frame_id, target_id):
        if len(self.data) < 10:
            return
        if self.is_stand:
            if self.check_stand2fall():
                print("frame-" + str(frame_id) + "," + "target-" + str(target_id) + " : ", end="")
                self.stand2fall()
            elif self.check_stand2sit():
                print("frame-" + str(frame_id) + "," + "target-" + str(target_id) + " : ", end="")
                self.stand2sit()
            elif self.check_stand2walk():
                print("frame-" + str(frame_id) + "," + "target-" + str(target_id) + " : ", end="")
                self.stand2walk()
        elif self.is_walk:
            if self.check_stand2fall():
                print("frame-" + str(frame_id) + "," + "target-" + str(target_id) + " : ", end="")
                self.walk2fall()
            elif self.check_stand2sit():
                print("frame-" + str(frame_id) + "," + "target-" + str(target_id) + " : ", end="")
                self.walk2sit()
            elif self.check_walk2stand():
                print("frame-" + str(frame_id) + "," + "target-" + str(target_id) + " : ", end="")
                self.walk2stand()
        elif self.is_run:
            pass
        elif self.is_fall:
            if self.check_fall2stand():
                print("frame-" + str(frame_id) + "," + "target-" + str(target_id) + " : ", end="")
                self.fall2stand()
        elif self.is_sit:
            if self.check_sit2stand():
                print("frame-" + str(frame_id) + "," + "target-" + str(target_id) + " : ", end="")
                self.sit2stand()
            elif self.check_sit2fall():
                print("frame-" + str(frame_id) + "," + "target-" + str(target_id) + " : ", end="")
                self.sit2fall()


if __name__ == '__main__':
    target_cols_test = ['index', 'frame_id', 'target_id', 'pos_x', 'pos_y', 'pos_z', 'vx', 'vy', 'vz', 'ax', 'ay', 'az']
    machine = StateDetectionMachine()
    tgt = pd.read_csv("processed_data/fall_exp3.csv", header=None, names=target_cols_test)
    ANGLE = 20 / 180 * math.pi
    HEIGHT = 2
    del tgt['index']
    # tgt['temp_y'] = tgt['pos_y']
    # tgt['temp_z'] = tgt['pos_z']
    # tgt['pos_y'] = tgt['temp_y'] * math.cos(ANGLE) + tgt['temp_z'] * math.sin(ANGLE)
    # tgt['pos_z'] = tgt['temp_z'] * math.cos(ANGLE) - tgt['temp_y'] * math.sin(ANGLE) + HEIGHT
    # del tgt['temp_y']
    # del tgt['temp_z']
    # tgt = tgt.drop(tgt[(tgt['vx'] == 0) & (tgt['vy'] == 0) & (tgt['vz'] == 0)].index)
    # tgt.to_csv("fall_exp3.csv", header=False)
    for _, line in tgt.iterrows():
        machine.insert_data(line)
        machine.process(int(line['frame_id']), 0)
    print("stand -> fall : ", str(machine.stand2fall_cnt))
    print("fall -> stand : ", str(machine.fall2stand_cnt))
    print("stand -> sit : ", str(machine.stand2sit_cnt))
    print("sit -> stand : ", str(machine.sit2stand_cnt))
