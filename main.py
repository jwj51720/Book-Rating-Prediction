import time
import argparse
import pandas as pd

from src import seed_everything

from src.data import context_data_load, context_data_split, context_data_loader
from src.data import dl_data_load, dl_data_split, dl_data_loader
from src.data import image_data_load, image_data_split, image_data_loader
from src.data import text_data_load, text_data_split, text_data_loader
from src.data import tree_data_load, tree_data_split, tree_data_loader

from src import FactorizationMachineModel, FieldAwareFactorizationMachineModel
from src import NeuralCollaborativeFiltering, WideAndDeepModel, DeepCrossNetworkModel
from src import CNN_FM
from src import DeepCoNN
from src import DecisionTreeModel

import itertools
import pandas as pd
import argparse
from tqdm import tqdm


def main(args):
    seed_everything(args.SEED)

    # model info
    model_info = f"MODEL_{args.MODEL}__EPOCHS_{args.EPOCHS}__TESTSIZE_{args.TEST_SIZE}__BATCH_{args.BATCH_SIZE}__LR_{args.LR}__NCFEMBEDDIM_{args.NCF_EMBED_DIM}__NCFMLPDIMS_{args.NCF_MLP_DIMS}__NCF_DROPOUT_{args.NCF_DROPOUT}"

    ######################## DATA LOAD
    print(f"--------------- {model_info} Load Data ---------------")
    if args.MODEL in ("FM", "FFM"):
        data = context_data_load(args)
    elif args.MODEL in ("NCF", "WDN", "DCN"):
        data = dl_data_load(args)
    elif args.MODEL == "CNN_FM":
        data = image_data_load(args)
    elif args.MODEL == "DeepCoNN":
        import nltk

        nltk.download("punkt")
        data = text_data_load(args)
    elif args.MODEL == "CATBOOST":
        data = tree_data_load(args)
    else:
        pass

    ######################## Train/Valid Split
    print(f"--------------- {model_info} Train/Valid Split ---------------")
    if args.MODEL in ("FM", "FFM"):
        data = context_data_split(args, data)
        data = context_data_loader(args, data)

    elif args.MODEL in ("NCF", "WDN", "DCN"):
        # data = dl_data_split(args, data)
        data = dl_data_split(args, data)
        # data = dl_data_loader(args, data)
        data = dl_data_loader(args, data)

    elif args.MODEL == "CNN_FM":
        data = image_data_split(args, data)
        data = image_data_loader(args, data)

    elif args.MODEL == "DeepCoNN":
        data = text_data_split(args, data)
        data = text_data_loader(args, data)

    elif args.MODEL == "CATBOOST":
        data = tree_data_split(args, data)
        data = tree_data_loader(args, data)
    else:
        pass

    ######################## Model
    print(f"--------------- INIT {model_info} ---------------")
    if args.MODEL == "FM":
        model = FactorizationMachineModel(args, data)
    elif args.MODEL == "FFM":
        model = FieldAwareFactorizationMachineModel(args, data)
    elif args.MODEL == "NCF":
        model = NeuralCollaborativeFiltering(args, data)
    elif args.MODEL == "WDN":
        model = WideAndDeepModel(args, data)
    elif args.MODEL == "DCN":
        model = DeepCrossNetworkModel(args, data)
    elif args.MODEL == "CNN_FM":
        model = CNN_FM(args, data)
    elif args.MODEL == "DeepCoNN":
        model = DeepCoNN(args, data)
    elif args.MODEL == "CATBOOST":
        model = DecisionTreeModel(args, data)
    else:
        pass

    ######################## TRAIN
    print(f"--------------- {model_info} TRAINING ---------------")
    valid_loss, return_epoch = model.train()

    ######################## INFERENCE
    print(f"--------------- {model_info} PREDICT ---------------")
    if args.MODEL in ("FM", "FFM", "NCF", "WDN", "DCN"):
        predicts = model.predict(data["test_dataloader"])
    elif args.MODEL == "CNN_FM":
        predicts = model.predict(data["test_dataloader"])
    elif args.MODEL == "DeepCoNN":
        predicts = model.predict(data["test_dataloader"])
    elif args.MODEL == "CATBOOST":
        predicts = model.predict(data["test_dataloader"])
    else:
        pass

    ######################## RULE-BASED
    print(f"--------------- RULE BASED ---------------")

    ######################## SAVE PREDICT
    print(f"--------------- SAVE {model_info} PREDICT ---------------")
    submission = pd.read_csv(args.DATA_PATH + "sample_submission.csv")
    if args.MODEL in (
        "FM",
        "FFM",
        "NCF",
        "WDN",
        "DCN",
        "CNN_FM",
        "DeepCoNN",
        "CATBOOST",
    ):
        submission["rating"] = predicts
    else:
        pass

    now = time.localtime()
    now_date = time.strftime("%Y%m%d", now)
    now_hour = time.strftime("%X", now)
    save_time = now_date + "_" + now_hour.replace(":", "")
    # submission.to_csv("submit/{}_{}.csv".format(save_time, args.MODEL), index=False)
    filename = (
        f"submit/LOSS_{round(valid_loss, 3)}__EPOCHS_{return_epoch}__{model_info}.csv"
    )
    submission.to_csv(filename, index=False)

    return valid_loss, return_epoch


if __name__ == "__main__":

    args_dict = {
        "MODEL": ["NCF"],
        "BATCH_SIZE": [128, 256],
        "NCF_EMBED_DIM": [24, 40, 48, 56, 64, 80, 96, 128, 256],
        "NCF_MLP_DIMS": [
            (256, 128, 128, 64),
            (256, 128, 128, 64, 32),
            (256, 256, 128, 64)
        ],
        "NCF_DROPOUT": [0.1, 0.2]
    }

    # args 종류 저장
    keys = list(args_dict.keys())
    n = len(keys)
    df = pd.DataFrame(columns=keys)
    df["loss"] = 9999

    # 가능한 경우의 수 모두 탐색
    for idx, x in enumerate(itertools.product(*args_dict.values())):

        # args = []
        # for i in range(n):
        #     args.append(f"{keys[i]} {x[i]}")

        # exe = "python main.py " + " ".join(args)
        # # print(exe)
        # subprocess.call(exe, shell=True)

        # 파서 선언 및 기본 값 지정
        parser = argparse.ArgumentParser(description="parser")
        arg = parser.add_argument

        ############### BASIC OPTION
        arg(
            "--DATA_PATH",
            type=str,
            default="data/",
            help="Data path를 설정할 수 있습니다.",
        )
        arg(
            "--MODEL",
            type=str,
            choices=["FM", "FFM", "NCF", "WDN", "DCN", "CNN_FM", "DeepCoNN", "CATBOOST"],
            help="학습 및 예측할 모델을 선택할 수 있습니다.",
        )
        arg("--DATA_SHUFFLE", type=bool, default=True, help="데이터 셔플 여부를 조정할 수 있습니다.")
        arg(
            "--TEST_SIZE", type=float, default=0.2, help="Train/Valid split 비율을 조정할 수 있습니다."
        )
        arg("--SEED", type=int, default=42, help="seed 값을 조정할 수 있습니다.")
        arg("--RULE-BASED", type=bool, default=False, help="rule-based 적용 할래 말래?")

        ############### TRAINING OPTION
        arg("--BATCH_SIZE", type=int, default=1024, help="Batch size를 조정할 수 있습니다.")
        arg("--EPOCHS", type=int, default=1, help="Epoch 수를 조정할 수 있습니다.")
        arg("--LR", type=float, default=1e-3, help="Learning Rate를 조정할 수 있습니다.")
        arg(
            "--WEIGHT_DECAY",
            type=float,
            default=1e-6,
            help="Adam optimizer에서 정규화에 사용하는 값을 조정할 수 있습니다.",
        )

        ############### GPU
        arg(
            "--DEVICE",
            type=str,
            default="cuda",
            choices=["cuda", "cpu"],
            help="학습에 사용할 Device를 조정할 수 있습니다.",
        )

        ############### FM
        arg("--FM_EMBED_DIM", type=int, default=16, help="FM에서 embedding시킬 차원을 조정할 수 있습니다.")

        ############### FFM
        arg(
            "--FFM_EMBED_DIM",
            type=int,
            default=16,
            help="FFM에서 embedding시킬 차원을 조정할 수 있습니다.",
        )

        ############### NCF
        arg(
            "--NCF_EMBED_DIM",
            type=int,
            default=16,
            help="NCF에서 embedding시킬 차원을 조정할 수 있습니다.",
        )
        arg(
            "--NCF_MLP_DIMS",
            type=list,
            default=(16, 16),
            help="NCF에서 MLP Network의 차원을 조정할 수 있습니다.",
        )
        arg(
            "--NCF_DROPOUT", type=float, default=0.2, help="NCF에서 Dropout rate를 조정할 수 있습니다."
        )

        ############### WDN
        arg(
            "--WDN_EMBED_DIM",
            type=int,
            default=16,
            help="WDN에서 embedding시킬 차원을 조정할 수 있습니다.",
        )
        arg(
            "--WDN_MLP_DIMS",
            type=list,
            default=(16, 16),
            help="WDN에서 MLP Network의 차원을 조정할 수 있습니다.",
        )
        arg(
            "--WDN_DROPOUT", type=float, default=0.2, help="WDN에서 Dropout rate를 조정할 수 있습니다."
        )

        ############### DCN
        arg(
            "--DCN_EMBED_DIM",
            type=int,
            default=16,
            help="DCN에서 embedding시킬 차원을 조정할 수 있습니다.",
        )
        arg(
            "--DCN_MLP_DIMS",
            type=list,
            default=(16, 16),
            help="DCN에서 MLP Network의 차원을 조정할 수 있습니다.",
        )
        arg(
            "--DCN_DROPOUT", type=float, default=0.2, help="DCN에서 Dropout rate를 조정할 수 있습니다."
        )
        arg(
            "--DCN_NUM_LAYERS",
            type=int,
            default=3,
            help="DCN에서 Cross Network의 레이어 수를 조정할 수 있습니다.",
        )

        ############### CNN_FM
        arg(
            "--CNN_FM_EMBED_DIM",
            type=int,
            default=64,
            help="CNN_FM에서 user와 item에 대한 embedding시킬 차원을 조정할 수 있습니다.",
        )
        arg(
            "--CNN_FM_LATENT_DIM",
            type=int,
            default=8,
            help="CNN_FM에서 user/item/image에 대한 latent 차원을 조정할 수 있습니다.",
        )
        arg(
            "--CNN_FM_LOAD_MODEL",
            type=bool,
            default=False,
            help="CNN_FM에서 학습된 parameter를 불러올 수 있습니다.",
        )

        ############### DeepCoNN
        arg(
            "--DEEPCONN_VECTOR_CREATE",
            type=bool,
            default=False,
            help="DEEP_CONN에서 text vector 생성 여부를 조정할 수 있으며 최초 학습에만 True로 설정하여야합니다.",
        )
        arg(
            "--DEEPCONN_EMBED_DIM",
            type=int,
            default=32,
            help="DEEP_CONN에서 user와 item에 대한 embedding시킬 차원을 조정할 수 있습니다.",
        )
        arg(
            "--DEEPCONN_LATENT_DIM",
            type=int,
            default=10,
            help="DEEP_CONN에서 user/item/image에 대한 latent 차원을 조정할 수 있습니다.",
        )
        arg(
            "--DEEPCONN_CONV_1D_OUT_DIM",
            type=int,
            default=50,
            help="DEEP_CONN에서 1D conv의 출력 크기를 조정할 수 있습니다.",
        )
        arg(
            "--DEEPCONN_KERNEL_SIZE",
            type=int,
            default=3,
            help="DEEP_CONN에서 1D conv의 kernel 크기를 조정할 수 있습니다.",
        )
        arg(
            "--DEEPCONN_WORD_DIM",
            type=int,
            default=768,
            help="DEEP_CONN에서 1D conv의 입력 크기를 조정할 수 있습니다.",
        )
        arg(
            "--DEEPCONN_OUT_DIM",
            type=int,
            default=32,
            help="DEEP_CONN에서 1D conv의 출력 크기를 조정할 수 있습니다.",
        )
        arg(
            "--DEEPCONN_LOAD_MODEL",
            type=bool,
            default=False,
            help="DEEP_CONN에서 학습된 parameter를 불러올 수 있습니다.",
        )

        ############### CatBoost
        arg(
            "--CATBOOST_ITERS",
            type=int,
            default=10,
            help="CATBOOST iterations 설정.",
        )
        arg(
            "--CATBOOST_DEPTH",
            type=int,
            default=None,
            help="CATBOOST depth 설정.",
        )

        args = parser.parse_args()

        # 그 외 args 값 추가
        for i in range(n):
            # print(f"{keys[i]}", f"{x[i]}")
            key = keys[i]
            value = x[i]
            if key == "MODEL":
                exe = f"args.{key} = '{value}'"

            else:
                exe = f"args.{key} = {value}"

            exec(exe)
            # arg(keys[i][0], default=x[i], type=keys[i][1])

        loss = main(args)

        x = list(x)
        x.append(loss)

        df.loc[idx] = x

    df.to_csv(f'tuning_result/{args_dict["MODEL"][0]}.csv', index=False)
