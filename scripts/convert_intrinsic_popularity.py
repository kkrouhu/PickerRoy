from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="把 IIPA ResNet-50 权重安全转换为 PickerRoy 使用的 ONNX。")
    parser.add_argument("weights", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    import torch
    import torchvision.models

    model = torchvision.models.resnet50(weights=None)
    model.fc = torch.nn.Linear(in_features=2048, out_features=1)
    # weights_only=True prevents arbitrary pickle objects from being deserialized.
    state = torch.load(args.weights, map_location="cpu", weights_only=True)
    if not isinstance(state, dict) or not all(isinstance(value, torch.Tensor) for value in state.values()):
        raise TypeError("权重文件不是纯张量 state_dict，已拒绝转换")
    model.load_state_dict(state, strict=True)
    model.eval()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    dummy = torch.zeros(1, 3, 224, 224, dtype=torch.float32)
    torch.onnx.export(
        model,
        dummy,
        args.output,
        input_names=["image"],
        output_names=["popularity"],
        dynamic_axes={"image": {0: "batch"}, "popularity": {0: "batch"}},
        opset_version=17,
        do_constant_folding=True,
        dynamo=False,
    )
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
