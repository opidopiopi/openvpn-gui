from nicegui import ui
from openvpn import connection


class BytecountGraph:
    def __init__(self, max_count: int):
        self._max_count: int = 300

        self.last = connection.Bytecount(0, 0)

        byte_formatter: str = '''
        function (value) {
            power = Math.floor(Math.log(value) / Math.log(1024))

            const prefix = ['B/s', 'KiB/s', 'MiB/s', 'GiB/s', 'TiB/s', 'I dont think so']
            value = Math.floor(value / (power * 1024))
            if (value < 1 || !isFinite(value)) {
                return ''
            }
            return `${value} ${prefix[power] || '?'}`
        }
        '''
        self._bandwidth_chart: ui.echart = ui.echart({
            'xAxis': {
                'type': 'category',
                'show': False},
            'yAxis': {
                'type': 'value',
                'axisLabel': {
                    ':formatter': byte_formatter}},
            'legend': {
                'show': 'false'},
            'series': [
                {'type': 'line',
                 'smooth': True,
                 'color': '#ea7e20',
                 'areaStyle': {'color': '#ea7e20'},
                 'showSymbol': False,
                 'name': 'Bytes in',
                 'data': [0] * self._max_count},
                {'type': 'line',
                 'smooth': True,
                 'color': '#003366',
                 'areaStyle': {'color': '#003366'},
                 'showSymbol': False,
                 'name': 'Bytes out',
                 'data': [0] * self._max_count},
            ],
        }).classes('col-span-full')

    def update_graph(self, bytecount: connection.Bytecount) -> None:
        chart_in_data = self._bandwidth_chart.options['series'][0]['data']
        chart_out_data = self._bandwidth_chart.options['series'][1]['data']

        chart_in_data.append(bytecount.bytes_incoming - self.last.bytes_incoming)
        chart_out_data.append(bytecount.bytes_outgoing - self.last.bytes_outgoing)

        self.last = bytecount

        if len(chart_in_data) > self._max_count:
            chart_in_data.pop(0)
            chart_out_data.pop(0)
