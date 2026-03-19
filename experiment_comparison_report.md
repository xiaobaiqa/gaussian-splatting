# Gaussian Splatting 实验对比报告

## 1. 实验设置

- 场景目录：`/workspaces/ai_slam_project/gaussian-splatting/data/video_jobs/input2_compare/scene`
- 原始视频：`/workspaces/ai_slam_project/gaussian-splatting/data/video_jobs/input2.mp4`
- 抽帧方式：`1 fps`，共 22 帧
- COLMAP 最终注册图像数：10 张
- 训练轮数：`1000`
- 评测划分：`ggbond`，当前场景测试视角数为 2

说明：

- `densify_grad_threshold` 越低，Gaussian 生长越激进。
- `lambda_dssim` 越高，损失函数越偏向结构相似性。
- `opacity_reset_interval` 越小，opacity 被重置得越频繁。
- `densification_interval` 越小，densify 触发得越频繁。

---

## 2. 实验一：生长阈值 `densify_grad_threshold`

固定设置：

- `lambda_dssim = 0.2`
- `iterations = 1000`

### 2.1 结果对比

| densify_grad_threshold | 最终 Gaussian 数 | SSIM | PSNR | LPIPS |
| --- | ---: | ---: | ---: | ---: |
| 0.0002 | 5937 | 0.8437 | 21.3083 | 0.3244 |
| 0.0001 | 8582 | 0.8504 | 21.5954 | 0.3176 |
| 0.00005 | 10994 | 0.8503 | 21.5547 | 0.3094 |

### 2.2 生长快照

| densify_grad_threshold | Iter 600 | Iter 700 | Iter 800 | Iter 900 | Iter 1000 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.0002 | 800 | 1361 | 2314 | 3775 | 5937 |
| 0.0001 | 883 | 1597 | 2894 | 5140 | 8582 |
| 0.00005 | 957 | 1780 | 3318 | 6159 | 10994 |

### 2.3 结论

- 从 `0.0002` 降到 `0.0001` 是明显有效的，三项指标都提升了。
- 从 `0.0001` 继续降到 `0.00005` 后，LPIPS 继续改善，但 SSIM 和 PSNR 没再提升，说明收益开始递减。
- 如果追求综合平衡，`0.0001` 是当前这段视频场景下最稳妥的选择。
- 如果更在意感知质量而不是模型规模，`0.00005` 也值得保留关注，因为它的 LPIPS 最优。

### 2.4 当前推荐

- 推荐值：`densify_grad_threshold = 0.0001`

---

## 3. 实验二：损失权重 `lambda_dssim`

固定设置：

- `densify_grad_threshold = 0.0001`
- `iterations = 1000`

### 3.1 结果对比

| lambda_dssim | 最终 Gaussian 数 | SSIM | PSNR | LPIPS |
| --- | ---: | ---: | ---: | ---: |
| 0.1 | 7741 | 0.8398 | 20.9259 | 0.3251 |
| 0.2 | 8582 | 0.8504 | 21.5954 | 0.3176 |
| 0.3 | 9043 | 0.8438 | 21.0371 | 0.3198 |

### 3.2 生长快照

| lambda_dssim | Iter 600 | Iter 700 | Iter 800 | Iter 900 | Iter 1000 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.1 | 868 | 1524 | 2733 | 4731 | 7741 |
| 0.2 | 883 | 1597 | 2894 | 5140 | 8582 |
| 0.3 | 897 | 1616 | 2943 | 5293 | 9043 |

### 3.3 结论

- `lambda_dssim = 0.2` 在三项指标上都是最好的。
- `0.1` 太偏向 L1，在这个场景里效果最差。
- `0.3` 虽然让模型更大一些，但并没有带来更好的指标，反而整体弱于 `0.2`。
- 当前默认值 `0.2` 对这段视频场景来说是一个很好的工作点。

### 3.4 当前推荐

- 推荐值：`lambda_dssim = 0.2`

---

## 4. 实验三：透明度重置频率 `opacity_reset_interval`

固定设置：

- `densify_grad_threshold = 0.0001`
- `lambda_dssim = 0.2`
- `iterations = 1000`

### 4.1 结果对比

| opacity_reset_interval | 最终 Gaussian 数 | SSIM | PSNR | LPIPS |
| --- | ---: | ---: | ---: | ---: |
| 200 | 7346 | 0.8184 | 19.4103 | 0.3490 |
| 500 | 8127 | 0.8172 | 18.8378 | 0.3445 |
| 800 | 7716 | 0.8161 | 18.9432 | 0.3479 |

### 4.2 生长快照

| opacity_reset_interval | Iter 600 | Iter 700 | Iter 800 | Iter 900 | Iter 1000 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 200 | 840 | 1497 | 2630 | 4481 | 7346 |
| 500 | 823 | 1532 | 2771 | 4847 | 8127 |
| 800 | 883 | 1603 | 2925 | 4628 | 7716 |

### 4.3 观察

- 这组三档的指标都明显差于我们当前最佳基线 `opacity_reset_interval = 3000` 的结果。
- 尤其 `200` 和 `500`，训练过程中经常看到 `opacity_mean` 被打回到接近 `0.01`，说明重置太频繁，影响了遮挡和结构稳定形成。
- 虽然模型也在持续长大，但额外的 Gaussian 没有转化成更好的质量。

### 4.4 结论

- 对当前这个仅训练到 `1000` iter 的场景来说，过于频繁的 opacity 重置会明显伤害效果。
- 至少在这个实验规模下，`200 / 500 / 800` 都不值得替代原本的更大间隔设置。

### 4.5 当前推荐

- 继续保留较大的 `opacity_reset_interval`
- 现阶段不建议往更小的方向调

---

## 5. 实验四：densify 触发频率 `densification_interval`

固定设置：

- `densify_grad_threshold = 0.0001`
- `lambda_dssim = 0.2`
- `iterations = 1000`

### 5.1 结果对比

| densification_interval | 最终 Gaussian 数 | SSIM | PSNR | LPIPS |
| --- | ---: | ---: | ---: | ---: |
| 50 | 45373 | 0.8565 | 21.8008 | 0.2809 |
| 100 | 8582 | 0.8504 | 21.5954 | 0.3176 |
| 200 | 2875 | 0.8299 | 20.3429 | 0.3637 |

### 5.2 生长快照

| densification_interval | Iter 600 | Iter 700 | Iter 800 | Iter 900 | Iter 1000 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 50 | 1611 | 5206 | 13623 | 27745 | 45373 |
| 100 | 883 | 1597 | 2894 | 5140 | 8582 |
| 200 | 885 | 885 | 1586 | 1586 | 2875 |

### 5.3 观察

- `50` 这一档非常激进，Gaussian 数量暴涨，但这次并不是单纯的“白长”，三项指标都进一步提升了。
- `100` 是当前比较均衡的中间档，模型规模明显更可控。
- `200` 过于保守，densify 次数太少，质量明显掉下去了。

### 5.4 结论

- 这说明“densify 的节奏”在这个场景里非常关键。
- 如果机器资源允许，`50` 在当前这段视频场景上是目前效果最好的设置。
- 但它的代价非常明显：最终 Gaussian 数达到 `45373`，远高于 `100` 档的 `8582`。

### 5.5 当前推荐

- 追求效果优先：`densification_interval = 50`
- 追求平衡：`densification_interval = 100`

---

## 6. 目前的综合结论

基于目前这四组实验，在这个视频场景和 `1000` iter 小规模设置下：

### 6.1 最均衡的一组

- `densify_grad_threshold = 0.0001`
- `lambda_dssim = 0.2`
- `densification_interval = 100`
- `opacity_reset_interval` 保持较大，不要过小

### 6.2 最强效果导向的一组

- `densify_grad_threshold = 0.0001`
- `lambda_dssim = 0.2`
- `densification_interval = 50`
- `opacity_reset_interval` 不要频繁重置

这组会更贵，但当前指标最好。

---

## 7. 当前推荐命令

### 7.1 平衡版

```bash
python3 train.py \
  -s /workspaces/ai_slam_project/gaussian-splatting/data/video_jobs/input2_compare/scene \
  --iterations 1000 \
  --eval \
  --densify_grad_threshold 0.0001 \
  --lambda_dssim 0.2 \
  --densification_interval 100
```

### 7.2 效果优先版

```bash
python3 train.py \
  -s /workspaces/ai_slam_project/gaussian-splatting/data/video_jobs/input2_compare/scene \
  --iterations 1000 \
  --eval \
  --densify_grad_threshold 0.0001 \
  --lambda_dssim 0.2 \
  --densification_interval 50
```

---

## 8. 下一步建议

1. 用“平衡版”和“效果优先版”各跑一次更长训练，例如 `3000` iter。
2. 如果 `50` 档在更长训练下继续保持优势，再看显存和渲染速度是否还能接受。
3. 如果你开始更关注部署或实时性，就应该围绕 Gaussian 数量做约束，而不是继续单纯追指标。

---

## 9. 实验五：高帧率输入 + 长训练

这组实验的目标不是继续微调单个超参数，而是验证一件更基础的事：

- 如果从同一个视频里抽取更多图片，让 COLMAP 建出更密、更完整的初始点云，再配合更长训练，最终效果会不会显著提升？

### 9.1 实验设置

- 原始视频：`/workspaces/ai_slam_project/gaussian-splatting/data/video_jobs/input2.mp4`
- 新场景目录：`/workspaces/ai_slam_project/gaussian-splatting/data/video_jobs/input2_dense15_v1/scene`
- 抽帧方式：`15 fps`
- 抽帧数量：`324` 张
- COLMAP 注册图像数：`324 / 324`
- 初始稀疏点数量：`17517`
- 平均重投影误差：`0.9117 px`
- 训练轮数：`10000`

固定采用我们前面选出来的“平衡版”参数：

- `densify_grad_threshold = 0.0001`
- `lambda_dssim = 0.2`
- `densification_interval = 100`
- `opacity_reset_interval = 3000`

### 9.2 最终结果

| 实验 | 最终 Gaussian 数 | 模型大小 | SSIM | PSNR | LPIPS |
| --- | ---: | ---: | ---: | ---: | ---: |
| 高帧率 + 长训练 | 721245 | 169M | 0.9575 | 33.0342 | 0.1349 |

### 9.3 训练观察

- 高帧率输入显著提升了 COLMAP 的重建质量，和之前 `1 fps / 22` 张图的小场景相比，这次不是“少量图注册成功”，而是全部 `324` 张图都注册进了重建。
- 初始点云从之前的小场景规模直接提升到 `17517` 个点，给 Gaussian 初始化提供了更扎实的几何起点。
- 在 `10000` 轮训练中，Gaussian 数量经历了明显增长，最高一度超过 `85` 万，后续在 prune 和 opacity reset 作用下回落并稳定到 `72` 万左右。
- 最终 loss 收敛到了 `0.016` 左右，测试指标相对前面的 `1000` 轮小实验有了非常大的提升。

### 9.4 结论

- 这组实验非常清楚地说明：对这个视频场景来说，“输入视角密度”比继续在极少量图像上抠小超参更重要。
- 当 COLMAP 能从更密的视频帧里恢复出更完整的几何和相机轨迹时，Gaussian Splatting 的训练上限会明显提高。
- 同时，这也带来了一个新的工程问题：模型规模急剧变大，最终 `point_cloud.ply` 达到 `169M`，Gaussian 数达到 `721245`，已经进入“效果很好，但部署成本高”的区间。

### 9.5 当前建议

- 如果目标是先把质量做出来，这组设置已经是一个很强的高质量基线。
- 如果下一步更关注实时性、存储或部署，最值得做的方向就不再是继续加密，而是围绕这组高质量结果做压缩和轻量化。
