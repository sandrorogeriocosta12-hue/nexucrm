import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import psutil
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from redis import Redis
from flask import current_app

from app.models import db, SystemMetric, PerformanceLog, CacheHit

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor de performance em tempo real"""

    def __init__(self):
        self.redis = Redis.from_url(current_app.config['REDIS_URL'])
        self.metrics_cache = {}

    def collect_system_metrics(self) -> Dict:
        """
        Coleta métricas do sistema
        """
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'cpu': {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'frequency': psutil.cpu_freq().current if psutil.cpu_freq() else None
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent,
                'used': psutil.virtual_memory().used
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'percent': psutil.disk_usage('/').percent,
                'free': psutil.disk_usage('/').free
            },
            'network': {
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv
            },
            'process': {
                'memory_percent': psutil.Process().memory_percent(),
                'cpu_percent': psutil.Process().cpu_percent(interval=1)
            }
        }

        # Salvar no banco
        self._save_metrics_to_db(metrics)

        # Cache em Redis
        self.redis.setex(
            f'system_metrics:{datetime.utcnow().strftime("%Y%m%d%H")}',
            3600,
            str(metrics)
        )

        return metrics

    def _save_metrics_to_db(self, metrics: Dict):
        """Salva métricas no banco de dados"""
        try:
            system_metric = SystemMetric(
                cpu_percent=metrics['cpu']['percent'],
                memory_percent=metrics['memory']['percent'],
                disk_percent=metrics['disk']['percent'],
                network_sent=metrics['network']['bytes_sent'],
                network_recv=metrics['network']['bytes_recv'],
                process_memory=metrics['process']['memory_percent'],
                process_cpu=metrics['process']['cpu_percent']
            )

            db.session.add(system_metric)
            db.session.commit()

        except Exception as e:
            logger.error(f"Erro ao salvar métricas: {str(e)}")
            db.session.rollback()

    def monitor_endpoint_performance(self, endpoint: str, method: str,
                                     duration: float, status_code: int) -> None:
        """
        Monitora performance de endpoints
        """
        log = PerformanceLog(
            endpoint=endpoint,
            method=method,
            duration_ms=duration * 1000,
            status_code=status_code,
            timestamp=datetime.utcnow()
        )

        db.session.add(log)
        db.session.commit()

        # Alertar se performance abaixo do esperado
        if duration > 2.0:  # Mais de 2 segundos
            self._trigger_performance_alert(endpoint, duration)

    def _trigger_performance_alert(self, endpoint: str, duration: float):
        """Dispara alerta de performance"""
        alert_key = f'performance_alert:{endpoint}:{datetime.utcnow().strftime("%Y%m%d")}'

        # Evitar alertas duplicados no mesmo dia
        if not self.redis.get(alert_key):
            self.redis.setex(alert_key, 86400, '1')

            # Enviar notificação
            self._send_performance_notification(endpoint, duration)

    def _send_performance_notification(self, endpoint: str, duration: float):
        """Envia notificação de performance"""
        # Implementar notificação (Slack, Email, etc.)
        message = f"⚠️ ALERTA DE PERFORMANCE\nEndpoint: {endpoint}\nDuração: {duration:.2f}s"
        logger.warning(message)

    def generate_performance_report(self, days: int = 7) -> Dict:
        """
        Gera relatório de performance
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Buscar logs de performance
        logs = PerformanceLog.query.filter(
            PerformanceLog.timestamp >= start_date
        ).all()

        if not logs:
            return {'error': 'Nenhum dado disponível'}

        # Agrupar por endpoint
        endpoint_stats = {}
        for log in logs:
            if log.endpoint not in endpoint_stats:
                endpoint_stats[log.endpoint] = {
                    'count': 0,
                    'total_duration': 0,
                    'errors': 0,
                    'durations': []
                }

            stats = endpoint_stats[log.endpoint]
            stats['count'] += 1
            stats['total_duration'] += log.duration_ms
            stats['durations'].append(log.duration_ms)

            if log.status_code >= 400:
                stats['errors'] += 1

        # Calcular estatísticas
        report = {
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': datetime.utcnow().strftime('%Y-%m-%d'),
                'days': days
            },
            'total_requests': len(logs),
            'endpoints': {}
        }

        for endpoint, stats in endpoint_stats.items():
            avg_duration = stats['total_duration'] / stats['count']
            error_rate = (stats['errors'] / stats['count']) * 100

            # Percentis
            durations = sorted(stats['durations'])
            p95 = durations[int(len(durations) * 0.95)] if durations else 0
            p99 = durations[int(len(durations) * 0.99)] if durations else 0

            report['endpoints'][endpoint] = {
                'request_count': stats['count'],
                'avg_duration_ms': round(avg_duration, 2),
                'p95_duration_ms': round(p95, 2),
                'p99_duration_ms': round(p99, 2),
                'error_rate': round(error_rate, 2),
                'performance_grade': self._calculate_performance_grade(avg_duration)
            }

        # Identificar endpoints problemáticos
        problematic = []
        for endpoint, stats in report['endpoints'].items():
            if stats['avg_duration_ms'] > 1000 or stats['error_rate'] > 5:
                problematic.append({
                    'endpoint': endpoint,
                    'avg_duration': stats['avg_duration_ms'],
                    'error_rate': stats['error_rate']
                })

        report['problematic_endpoints'] = problematic
        report['recommendations'] = self._generate_performance_recommendations(report)

        return report

    def _calculate_performance_grade(self, avg_duration: float) -> str:
        """Calcula nota de performance"""
        if avg_duration < 100:
            return 'A+'
        elif avg_duration < 200:
            return 'A'
        elif avg_duration < 500:
            return 'B'
        elif avg_duration < 1000:
            return 'C'
        else:
            return 'D'

    def _generate_performance_recommendations(self, report: Dict) -> List[str]:
        """Gera recomendações de otimização"""
        recommendations = []

        for endpoint, stats in report['endpoints'].items():
            if stats['performance_grade'] in ['C', 'D']:
                recommendations.append(
                    f"Otimizar endpoint '{endpoint}' - Duração média: {stats['avg_duration_ms']}ms"
                )

            if stats['error_rate'] > 5:
                recommendations.append(
                    f"Corrigir erros em '{endpoint}' - Taxa de erro: {stats['error_rate']}%"
                )

        return recommendations


class CacheOptimizer:
    """Otimizador de cache"""

    def __init__(self):
        self.redis = Redis.from_url(current_app.config['REDIS_URL'])
        self.cache_stats = {}

    def cache_get(self, key: str, ttl: int = 3600):
        """
        Obtém dado do cache com estatísticas
        """
        start_time = time.time()

        # Buscar do cache
        data = self.redis.get(key)

        duration = time.time() - start_time

        if data:
            # Cache hit
            self._record_cache_hit(key, duration, True)
            return data.decode('utf-8')
        else:
            # Cache miss
            self._record_cache_hit(key, duration, False)
            return None

    def cache_set(self, key: str, data: str, ttl: int = 3600):
        """
        Define dado no cache
        """
        self.redis.setex(key, ttl, data)

    def _record_cache_hit(self, key: str, duration: float, hit: bool):
        """Registra estatísticas de cache"""
        cache_key = key.split(':')[0] if ':' in key else key

        if cache_key not in self.cache_stats:
            self.cache_stats[cache_key] = {
                'hits': 0,
                'misses': 0,
                'total_duration': 0,
                'last_access': datetime.utcnow()
            }

        stats = self.cache_stats[cache_key]

        if hit:
            stats['hits'] += 1
        else:
            stats['misses'] += 1

        stats['total_duration'] += duration
        stats['last_access'] = datetime.utcnow()

        # Salvar no banco periodicamente
        if stats['hits'] + stats['misses'] % 100 == 0:
            self._save_cache_stats_to_db(cache_key, stats)

    def _save_cache_stats_to_db(self, cache_key: str, stats: Dict):
        """Salva estatísticas de cache no banco"""
        try:
            hit_rate = (stats['hits'] / (stats['hits'] + stats['misses'])) * 100 if (stats['hits'] + stats['misses']) > 0 else 0

            cache_hit = CacheHit(
                cache_key=cache_key,
                hits=stats['hits'],
                misses=stats['misses'],
                hit_rate=hit_rate,
                avg_duration_ms=(stats['total_duration'] / (stats['hits'] + stats['misses'])) * 1000,
                recorded_at=datetime.utcnow()
            )

            db.session.add(cache_hit)
            db.session.commit()

        except Exception as e:
            logger.error(f"Erro ao salvar estatísticas de cache: {str(e)}")

    def get_cache_analytics(self) -> Dict:
        """
        Retorna analytics do cache
        """
        # Buscar estatísticas do Redis
        info = self.redis.info()

        # Calcular taxa de hit/miss
        total_hits = sum(stats['hits'] for stats in self.cache_stats.values())
        total_misses = sum(stats['misses'] for stats in self.cache_stats.values())
        total_accesses = total_hits + total_misses

        hit_rate = (total_hits / total_accesses * 100) if total_accesses > 0 else 0

        # Identificar caches ineficientes
        inefficient_caches = []
        for key, stats in self.cache_stats.items():
            key_hit_rate = (stats['hits'] / (stats['hits'] + stats['misses'])) * 100 if (stats['hits'] + stats['misses']) > 0 else 0
            if key_hit_rate < 20:  # Taxa de hit menor que 20%
                inefficient_caches.append({
                    'key': key,
                    'hit_rate': round(key_hit_rate, 2),
                    'total_accesses': stats['hits'] + stats['misses']
                })

        return {
            'redis': {
                'used_memory': info['used_memory_human'],
                'total_keys': info['db0']['keys'] if 'db0' in info else 0,
                'connections': info['connected_clients'],
                'uptime_days': info['uptime_in_days']
            },
            'cache_performance': {
                'total_hits': total_hits,
                'total_misses': total_misses,
                'hit_rate': round(hit_rate, 2),
                'avg_duration_ms': sum(stats['total_duration'] for stats in self.cache_stats.values()) / total_accesses * 1000 if total_accesses > 0 else 0
            },
            'inefficient_caches': inefficient_caches,
            'recommendations': self._generate_cache_recommendations(hit_rate, inefficient_caches)
        }

    def _generate_cache_recommendations(self, hit_rate: float, inefficient_caches: List) -> List[str]:
        """Gera recomendações para otimização de cache"""
        recommendations = []

        if hit_rate < 50:
            recommendations.append("❌ Taxa de cache hit muito baixa. Revisar estratégia de cache.")

        for cache in inefficient_caches:
            recommendations.append(
                f"🔍 Cache '{cache['key']}' tem apenas {cache['hit_rate']}% de hit rate"
            )

        if len(inefficient_caches) > 5:
            recommendations.append("🚨 Muitos caches ineficientes. Considerar remover ou otimizar.")

        return recommendations


class DatabaseOptimizer:
    """Otimizador de banco de dados"""

    @staticmethod
    def optimize_queries():
        """
        Otimiza queries do banco de dados
        """
        # Analisar queries lentas
        slow_queries = DatabaseOptimizer._find_slow_queries()

        # Criar índices para queries lentas
        for query in slow_queries:
            DatabaseOptimizer._create_index_if_needed(query)

        # Limpar dados antigos
        DatabaseOptimizer._cleanup_old_data()

        # Vacuum/optimize (dependendo do banco)
        DatabaseOptimizer._vacuum_database()

    @staticmethod
    def _find_slow_queries() -> List[Dict]:
        """
        Encontra queries lentas (PostgreSQL específico)
        """
        try:
            # Query para encontrar queries lentas no PostgreSQL
            query = """
            SELECT query, mean_time, calls
            FROM pg_stat_statements
            WHERE mean_time > 100 -- Mais de 100ms
            ORDER BY mean_time DESC
            LIMIT 10;
            """

            result = db.session.execute(query)
            slow_queries = []

            for row in result:
                slow_queries.append({
                    'query': row[0][:100],  # Primeiros 100 caracteres
                    'mean_time': row[1],
                    'calls': row[2]
                })

            return slow_queries

        except Exception as e:
            logger.error(f"Erro ao buscar queries lentas: {str(e)}")
            return []

    @staticmethod
    def _create_index_if_needed(query_info: Dict):
        """
        Cria índice se necessário para query lenta
        """
        query = query_info['query'].lower()

        # Análise simples para determinar colunas para índice
        if 'where' in query:
            # Extrair condições WHERE (simplificado)
            where_start = query.find('where') + 5
            where_clause = query[where_start:].split(' ')[:10]

            # Identificar colunas
            columns = []
            for word in where_clause:
                if word.endswith('_id') or word in ['created_at', 'updated_at', 'status']:
                    columns.append(word)

            if columns:
                # Criar índice (em produção, seria mais sofisticado)
                logger.info(f"Sugerindo índice para colunas: {columns}")
                # db.session.execute(f"CREATE INDEX IF NOT EXISTS idx_{columns[0]}_{columns[1] if len(columns)>1 else ''} ON ...")

    @staticmethod
    def _cleanup_old_data():
        """
        Limpa dados antigos para manter o banco otimizado
        """
        try:
            # Limpar logs antigos (mais de 90 dias)
            ninety_days_ago = datetime.utcnow() - timedelta(days=90)

            # Logs de performance
            PerformanceLog.query.filter(
                PerformanceLog.timestamp < ninety_days_ago
            ).delete(synchronize_session=False)

            # Logs de sistema
            SystemMetric.query.filter(
                SystemMetric.timestamp < ninety_days_ago
            ).delete(synchronize_session=False)

            # Conversas antigas (mantém 180 dias)
            hundred_eighty_days_ago = datetime.utcnow() - timedelta(days=180)
            from app.models import Conversation
            Conversation.query.filter(
                Conversation.created_at < hundred_eighty_days_ago
            ).delete(synchronize_session=False)

            db.session.commit()

            logger.info("Dados antigos limpos com sucesso")

        except Exception as e:
            logger.error(f"Erro ao limpar dados antigos: {str(e)}")
            db.session.rollback()

    @staticmethod
    def _vacuum_database():
        """
        Executa VACUUM no PostgreSQL para otimização
        """
        try:
            # VACUUM analisa
            db.session.execute("VACUUM ANALYZE;")
            db.session.commit()
            logger.info("VACUUM ANALYZE executado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao executar VACUUM: {str(e)}")


class AutoScaler:
    """Sistema de auto-scaling baseado em demanda"""

    def __init__(self):
        self.redis = Redis.from_url(current_app.config['REDIS_URL'])

    def analyze_traffic_patterns(self) -> Dict:
        """
        Analisa padrões de tráfego para scaling
        """
        # Coletar métricas da última hora
        hour_ago = datetime.utcnow() - timedelta(hours=1)

        # Requests por minuto
        requests = PerformanceLog.query.filter(
            PerformanceLog.timestamp >= hour_ago
        ).all()

        if not requests:
            return {'error': 'Dados insuficientes'}

        # Agrupar por minuto
        requests_by_minute = {}
        for req in requests:
            minute_key = req.timestamp.strftime('%Y-%m-%d %H:%M')
            requests_by_minute[minute_key] = requests_by_minute.get(minute_key, 0) + 1

        # Identificar picos
        avg_requests = sum(requests_by_minute.values()) / len(requests_by_minute)
        peak_requests = max(requests_by_minute.values())

        # Calcular necessidade de scaling
        scaling_factor = peak_requests / max(avg_requests, 1)

        recommendation = 'MAINTAIN'
        if scaling_factor > 2:
            recommendation = 'SCALE_UP'
        elif scaling_factor < 0.5:
            recommendation = 'SCALE_DOWN'

        return {
            'analysis_period': 'last_hour',
            'total_requests': len(requests),
            'avg_requests_per_minute': round(avg_requests, 2),
            'peak_requests_per_minute': peak_requests,
            'scaling_factor': round(scaling_factor, 2),
            'scaling_recommendation': recommendation,
            'peak_times': self._identify_peak_times(requests_by_minute)
        }

    def _identify_peak_times(self, requests_by_minute: Dict) -> List[Dict]:
        """Identifica horários de pico"""
        # Ordenar por volume
        sorted_times = sorted(
            requests_by_minute.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]  # Top 5 picos

        return [
            {'time': time, 'requests': count}
            for time, count in sorted_times
        ]

    def auto_scale_resources(self, analysis: Dict):
        """
        Executa auto-scaling baseado na análise
        """
        recommendation = analysis.get('scaling_recommendation')

        if recommendation == 'SCALE_UP':
            self._scale_up_resources(analysis)
        elif recommendation == 'SCALE_DOWN':
            self._scale_down_resources(analysis)

    def _scale_up_resources(self, analysis: Dict):
        """Escala recursos para cima"""
        logger.info(f"🔼 SCALING UP - Peak: {analysis['peak_requests_per_minute']} req/min")

        # Ações de scale-up:
        # 1. Aumentar workers do Celery
        # 2. Aumentar réplicas do serviço web
        # 3. Aumentar cache Redis

        # Implementação real dependeria do provedor de cloud
        # (AWS Auto Scaling, Kubernetes HPA, etc.)

        # Por enquanto, apenas log
        pass

    def _scale_down_resources(self, analysis: Dict):
        """Escala recursos para baixo"""
        logger.info(f"🔽 SCALING DOWN - Low traffic detected")

        # Ações de scale-down:
        # 1. Reduzir workers do Celery
        # 2. Reduzir réplicas do serviço web
        # 3. Otimizar cache

        pass