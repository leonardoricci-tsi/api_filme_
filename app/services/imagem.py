import io

from PIL import Image, ImageOps, UnidentifiedImageError

TAMANHO_MAXIMO_BYTES = 2 * 1024 * 1024
# Teto de pixels antes de decodificar: um PNG de poucos KB pode declarar
# 20000x20000 e explodir a memória ao abrir (decompression bomb).
PIXELS_MAXIMOS = 25_000_000
# A foto é reduzida pra caber nisso — perfil não precisa de 4000px.
LADO_MAXIMO = 1024

# Formato detectado pelo Pillow a partir dos bytes -> (extensão, content-type).
FORMATOS_ACEITOS = {
    "JPEG": ("jpg", "image/jpeg"),
    "PNG": ("png", "image/png"),
    "WEBP": ("webp", "image/webp"),
}


class ImagemInvalida(Exception):
    """Arquivo não é uma imagem aceita (formato, corrompido ou gigante)."""


class ImagemGrandeDemais(Exception):
    """Arquivo passou de TAMANHO_MAXIMO_BYTES."""


def processar_foto(conteudo: bytes) -> tuple[bytes, str, str]:
    """Valida e reencoda a foto de perfil. Devolve (bytes, extensão, content-type).

    O tipo é decidido pelos bytes, nunca pelo `Content-Type` nem pela
    extensão do nome do arquivo — os dois vêm do cliente e são só uma
    declaração. Reencodar também descarta tudo que não é pixel: metadados
    EXIF (inclusive a localização GPS de quem tirou a foto) e qualquer
    coisa escondida depois do fim da imagem."""
    if len(conteudo) > TAMANHO_MAXIMO_BYTES:
        raise ImagemGrandeDemais

    try:
        with Image.open(io.BytesIO(conteudo)) as imagem:
            formato = imagem.format
            largura, altura = imagem.size
            if formato not in FORMATOS_ACEITOS:
                raise ImagemInvalida
            if largura * altura > PIXELS_MAXIMOS:
                raise ImagemInvalida
            # verify() checa a integridade sem decodificar tudo — mas
            # inutiliza o objeto, por isso a imagem é reaberta abaixo.
            imagem.verify()

        with Image.open(io.BytesIO(conteudo)) as imagem:
            # Foto de celular costuma vir "deitada" com a rotação só no EXIF;
            # aplica antes de descartar o EXIF, senão ela fica torta.
            imagem = ImageOps.exif_transpose(imagem)
            imagem.thumbnail((LADO_MAXIMO, LADO_MAXIMO))
            if formato == "JPEG" and imagem.mode not in ("RGB", "L"):
                imagem = imagem.convert("RGB")
            saida = io.BytesIO()
            imagem.save(saida, format=formato)
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError) as erro:
        raise ImagemInvalida from erro

    extensao, content_type = FORMATOS_ACEITOS[formato]
    return saida.getvalue(), extensao, content_type
