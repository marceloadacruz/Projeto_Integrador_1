from django.core.management import BaseCommand

from Agendamento.models import Service


class Command(BaseCommand):
    SERVICOS = [
        {
            "name": "Tranças Soltas (Individuais)",
            "description": (
                "Box Braids, Knotless e French Curls. "
                "Perfeitas para quem busca movimento, comprimento e proteção dos fios "
                "com um acabamento impecável e natural."
            ),
            "price": 350.00,
            "duration": 360,
        },
        {
            "name": "Tranças Nagô (Rente à Raiz)",
            "description": (
                "Estilos rentes ao couro cabeludo, desde as linhas clássicas até "
                "desenhos artísticos e geométricos, como as tradicionais Fulani Braids."
            ),
            "price": 180.00,
            "duration": 120,
        },
        {
            "name": "Twists & Faux Locs",
            "description": (
                "Visual marcante com a técnica de duas mechas (corda) ou estética de dreads removíveis. "
                "Garante leveza, textura diferenciada e um estilo único."
            ),
            "price": 300.00,
            "duration": 270,
        },
        {
            "name": "Aplicação & Volume",
            "description": (
                "Transformação completa com Crochet Braids ou Entrelace. "
                "Ideal para quem deseja volume imediato e texturas de cabelos cacheados ou orgânicos."
            ),
            "price": 280.00,
            "duration": 240,
        },
        {
            "name": "Estilos Express & Penteados",
            "description": (
                "Opções rápidas e estilosas como tranças boxeadoras e rabos de cavalo. "
                "A escolha certa para eventos, festas ou para o dia a dia prático."
            ),
            "price": 90.00,
            "duration": 60,
        },
    ]

    def handle(self, *args, **options):
        Service.objects.registrar_servicos(self.SERVICOS)
