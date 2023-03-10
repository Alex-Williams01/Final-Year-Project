import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

import config
from classifier import Classifier


class ModalityFusion(nn.Module):
    """
        Produce a pytorch neural network module used for multi-modal fusion
        Attributes:
            weight_{1-3} - Weights used to control the impact of each modality
    """

    def __init__(self) -> None:
        """
            Initializes internal ModalityFusion state
        """
        super(ModalityFusion, self).__init__()
        self.weight_1 = nn.Parameter(torch.ones(1))
        self.weight_2 = nn.Parameter(torch.ones(1))
        self.weight_3 = nn.Parameter(torch.ones(1))

    def forward(self, text: Tensor, audio: Tensor, video: Tensor) -> Tensor:
        """
            Read the bert text embeddings

            :param text: A tensor representing the textual modality
            :param audio: A tensor representing the audio modality
            :param video: A tensor representing the video modality

            :return: A tensor containing the concatenated / fused output of the three input modalities
        """
        text_w = text * self.weight_1
        audio_w = audio * self.weight_2
        video_w = video * self.weight_3

        return torch.cat([text_w, audio_w, video_w], -1)


class SubNet(nn.Module):
    """
        Produce a pytorch neural network module used as a subnetwork for each modality
    """

    def __init__(self, in_size: int, hidden_size: int, dropout: float) -> None:
        """
            Initializes internal SubNet state
        """
        super(SubNet, self).__init__()
        self.norm = nn.BatchNorm1d(in_size)
        self.drop = nn.Dropout(p=dropout)
        self.linear_1 = nn.Linear(in_size, hidden_size)
        self.linear_2 = nn.Linear(hidden_size, hidden_size)
        self.linear_3 = nn.Linear(hidden_size, hidden_size)

    def forward(self, x: Tensor) -> Tensor:
        """
            Read the bert text embeddings

            :param x: A tensor representing the input modality

            :return: A tensor containing the output of the three layers
        """
        normed = self.norm(x)
        dropped = self.drop(normed)
        y_1 = F.relu(self.linear_1(dropped))
        y_2 = F.relu(self.linear_2(y_1))
        y_3 = F.relu(self.linear_3(y_2))
        return y_3


class WeightedMultiModalFusionNetwork(Classifier):
    """
        Produce a pytorch neural network module - final top-level multi-modal fusion network
    """

    def __init__(self, speaker_num) -> None:
        """
            Initializes internal WeightedMultiModalFusionNetwork state
        """
        super(WeightedMultiModalFusionNetwork, self).__init__()

        self.video_subnet = SubNet(config.VIDEO_DIM, config.VIDEO_HIDDEN, config.VIDEO_DROPOUT)
        self.audio_subnet = SubNet(config.AUDIO_DIM, config.AUDIO_HIDDEN, config.AUDIO_DROPOUT)
        self.text_subnet = SubNet(config.TEXT_DIM, config.TEXT_HIDDEN, config.TEXT_DROPOUT)
        self.context_subnet = SubNet(config.TEXT_DIM, config.CONTEXT_HIDDEN, config.CONTEXT_DROPOUT)
        self.speaker_subnet = SubNet(speaker_num, config.SPEAKER_HIDDEN, config.SPEAKER_DROPOUT)

        self.fusion = ModalityFusion()

        self.post_fusion_dropout = nn.Dropout(p=config.POST_FUSION_DROPOUT)

        self.post_fusion_layer_1 = nn.Linear(config.TEXT_HIDDEN + config.VIDEO_HIDDEN + config.AUDIO_HIDDEN,
                                             config.POST_FUSION_DIM)

        self.post_fusion_layer_2 = nn.Linear(config.POST_FUSION_DIM, config.POST_FUSION_DIM)

        self.post_fusion_layer_3 = nn.Linear(config.POST_FUSION_DIM + config.SPEAKER_HIDDEN + config.CONTEXT_HIDDEN,
                                             config.POST_FUSION_DIM)
        self.fc = nn.Linear(config.POST_FUSION_DIM, 2)

    def forward(self, text_x: Tensor, video_x: Tensor, audio_x: Tensor, speaker_x: Tensor, context_x: Tensor) -> Tensor:
        """
            Read the bert text embeddings

            :param context_x: A tensor representing the context feature
            :param speaker_x: A tensor representing the speaker feature
            :param audio_x: A tensor representing the audio modality
            :param video_x: A tensor representing the video modality
            :param text_x: A tensor representing the textual modality

            :return: A tensor containing the output of the model
        """
        video_h = self.video_subnet(video_x)
        audio_h = self.audio_subnet(audio_x)
        text_h = self.text_subnet(text_x)
        speaker_h = self.speaker_subnet(speaker_x)
        context_h = self.context_subnet(context_x)

        fusion_h = self.fusion(text_h, audio_h, video_h)

        x = self.post_fusion_dropout(fusion_h)

        x = F.relu(self.post_fusion_layer_1(x), inplace=True)

        x = self.post_fusion_dropout(x)

        x = F.relu(self.post_fusion_layer_2(x), inplace=True)

        late_fusion = torch.cat([x, speaker_h, context_h], dim=-1)

        x = self.post_fusion_dropout(late_fusion)

        x = F.relu(self.post_fusion_layer_3(x), inplace=True)

        x = self.post_fusion_dropout(x)

        return self.fc(x)
