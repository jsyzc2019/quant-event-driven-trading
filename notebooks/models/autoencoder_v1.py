import math

import torch
import torch.nn as nn
import torch.nn.functional as F


class PositionalEncoder(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super(PositionalEncoder, self).__init__()

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)

        self.register_buffer("pe", pe)

    def forward(self, x):
        pe_slice = self.pe[: x.size(0), :]
        return x + pe_slice


class AutoEncoder(nn.Module):
    def __init__(
        self,
        segment_length: int,
        n_features: int,
        latent_dim: int = 32,
        num_heads: int = 4,
        dropout_prob: float = 0.2,
        activation_type: str = "leaky_relu",
        use_attention: bool = True,
    ):
        super(AutoEncoder, self).__init__()
        self.use_attention = use_attention
        self.segment_length = segment_length
        self.n_features = n_features
        self.encoded_length = segment_length // 4
        self.activation_type = activation_type

        if self.use_attention:
            self.positional_encoder = PositionalEncoder(latent_dim)

        self.encoder = nn.Sequential(
            nn.Conv1d(self.n_features, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            self._get_activation(self.activation_type),
            nn.MaxPool1d(2),
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            self._get_activation(self.activation_type),
            nn.MaxPool1d(2),
            nn.AdaptiveAvgPool1d(self.encoded_length),
        )

        if use_attention:
            self.attention_encoder = nn.MultiheadAttention(
                embed_dim=latent_dim, num_heads=num_heads, dropout=dropout_prob
            )

        self.fc_encoder = nn.Sequential(
            nn.Linear(128 * self.encoded_length, 256),
            nn.LayerNorm(256),
            self._get_activation("tanh"),
            nn.Linear(256, latent_dim),
            nn.Dropout(dropout_prob),
        )

        self.fc_decoder = nn.Sequential(
            nn.Linear(latent_dim, 256),
            nn.LayerNorm(256),
            self._get_activation("tanh"),
            nn.Linear(256, 128 * self.encoded_length),
            nn.Dropout(dropout_prob),
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose1d(128, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            self._get_activation(self.activation_type),
            nn.Upsample(scale_factor=2),
            nn.ConvTranspose1d(64, self.n_features, kernel_size=3, padding=1),
            nn.BatchNorm1d(self.n_features),
            self._get_activation(self.activation_type),
            nn.Upsample(scale_factor=2),
        )

        self.residual = nn.Sequential(
            nn.Conv1d(self.n_features, self.n_features, kernel_size=3, padding=1),
            nn.BatchNorm1d(self.n_features),
            self._get_activation("relu"),
        )

        self.apply(self._init_weights)

    def forward(self, x):
        x = x.permute(0, 2, 1)
        identity = x.clone()

        encoded = self.encoder(x)
        encoded = encoded.view(encoded.size(0), -1)

        latent = self.fc_encoder(encoded)

        if self.use_attention:
            latent = latent.unsqueeze(1)
            latent = self.positional_encoder(latent)

            attn_encoded, _ = self.attention_encoder(latent, latent, latent)
            attn_encoded = self._get_activation(self.activation_type)(attn_encoded)
            latent = attn_encoded.squeeze(1)

        decoded = self.fc_decoder(latent)
        decoded = decoded.view(decoded.size(0), 128, self.encoded_length)
        decoded = self.decoder(decoded)
        decoded = decoded.permute(0, 2, 1)

        residual_out = self.residual(identity)
        residual_out = residual_out.permute(0, 2, 1)

        output = decoded + residual_out

        return output

    def get_latent(self, x, normalize=True):
        x = x.permute(0, 2, 1)

        encoded = self.encoder(x)
        encoded = encoded.view(encoded.size(0), -1)

        latent = self.fc_encoder(encoded)

        if normalize:
            latent = F.normalize(latent, p=2, dim=1)

        return latent

    @staticmethod
    def _get_activation(activation: str):
        activations = {
            "relu": nn.ReLU(),
            "leaky_relu": nn.LeakyReLU(negative_slope=0.01),
            "gelu": nn.GELU(),
            "tanh": nn.Tanh(),
            "swish": nn.SiLU(),
            "mish": nn.Mish(),
        }

        return activations.get(activation, nn.Tanh())

    def _init_weights(self, m):
        if isinstance(m, (nn.Conv1d, nn.ConvTranspose1d, nn.Linear)):
            if self.activation_type in ["relu", "leaky_relu"]:
                nn.init.kaiming_normal_(m.weight, nonlinearity=self.activation_type)
            else:
                nn.init.xavier_normal_(m.weight)
            if m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.BatchNorm1d) or isinstance(m, nn.LayerNorm):
            nn.init.constant_(m.weight, 1)
            nn.init.constant_(m.bias, 0)