"""Repositorios de acceso a datos para SQLite con aislamiento estricto por tenant (RN-05)."""

import sqlite3
from dataclasses import replace

from src.domain.models import (
    ESTADOS_ACTIVOS,
    Paciente,
    Profesional,
    Sillon,
    Tenant,
    Turno,
)


class RepositorioTenants:
    """Acceso a datos de clínicas / consultorios."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def guardar(self, tenant: Tenant) -> Tenant:
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO tenants (id, nombre)
                VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET nombre = excluded.nombre;
                """,
                (tenant.id, tenant.nombre),
            )
        return tenant

    def obtener_por_id(self, tenant_id: str) -> Tenant | None:
        cursor = self._conn.execute(
            "SELECT id, nombre FROM tenants WHERE id = ?;", (tenant_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Tenant(id=row["id"], nombre=row["nombre"])


class RepositorioProfesionales:
    """Acceso a datos de profesionales filtrados por tenant."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def _fila_a_profesional(self, row: sqlite3.Row) -> Profesional:
        return Profesional(
            id=row["id"],
            tenant_id=row["tenant_id"],
            nombre=row["nombre"],
            activo=bool(row["activo"]),
            matricula=row["matricula"] or "",
            especialidad=row["especialidad"] or "",
        )

    def guardar(self, profesional: Profesional) -> Profesional:
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO tenants (id, nombre) VALUES (?, ?);",
                (profesional.tenant_id, profesional.tenant_id),
            )
            self._conn.execute(
                """
                INSERT INTO profesionales (id, tenant_id, nombre, activo, matricula, especialidad)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    nombre = excluded.nombre,
                    activo = excluded.activo,
                    matricula = excluded.matricula,
                    especialidad = excluded.especialidad;
                """,
                (
                    profesional.id,
                    profesional.tenant_id,
                    profesional.nombre,
                    1 if profesional.activo else 0,
                    profesional.matricula,
                    profesional.especialidad,
                ),
            )
        return profesional

    def obtener_por_id(
        self, tenant_id: str, profesional_id: str
    ) -> Profesional | None:
        cursor = self._conn.execute(
            """
            SELECT id, tenant_id, nombre, activo, matricula, especialidad
            FROM profesionales
            WHERE tenant_id = ? AND id = ?;
            """,
            (tenant_id, profesional_id),
        )
        row = cursor.fetchone()
        return self._fila_a_profesional(row) if row else None

    def listar_por_tenant(
        self, tenant_id: str, solo_activos: bool | None = None
    ) -> list[Profesional]:
        filtros = ["tenant_id = ?"]
        params: list[object] = [tenant_id]
        if solo_activos is not None:
            filtros.append("activo = ?")
            params.append(1 if solo_activos else 0)
        where_clause = " AND ".join(filtros)
        cursor = self._conn.execute(
            f"""
            SELECT id, tenant_id, nombre, activo, matricula, especialidad
            FROM profesionales
            WHERE {where_clause}
            ORDER BY nombre ASC;
            """,
            tuple(params),
        )
        return [self._fila_a_profesional(row) for row in cursor.fetchall()]

    def obtener_o_crear(self, tenant_id: str, nombre: str) -> Profesional:
        cursor = self._conn.execute(
            """
            SELECT id, tenant_id, nombre, activo, matricula, especialidad
            FROM profesionales
            WHERE tenant_id = ? AND nombre = ?;
            """,
            (tenant_id, nombre),
        )
        row = cursor.fetchone()
        if row:
            return self._fila_a_profesional(row)
        profesional = Profesional(nombre=nombre, tenant_id=tenant_id)
        return self.guardar(profesional)


class RepositorioSillones:
    """Acceso a datos de sillones/boxes filtrados por tenant."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def _fila_a_sillon(self, row: sqlite3.Row) -> Sillon:
        return Sillon(
            id=row["id"],
            tenant_id=row["tenant_id"],
            nombre=row["nombre"],
            activo=bool(row["activo"]),
            equipamiento=row["equipamiento"] or "",
        )

    def guardar(self, sillon: Sillon) -> Sillon:
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO tenants (id, nombre) VALUES (?, ?);",
                (sillon.tenant_id, sillon.tenant_id),
            )
            self._conn.execute(
                """
                INSERT INTO sillones (id, tenant_id, nombre, activo, equipamiento)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    nombre = excluded.nombre,
                    activo = excluded.activo,
                    equipamiento = excluded.equipamiento;
                """,
                (
                    sillon.id,
                    sillon.tenant_id,
                    sillon.nombre,
                    1 if sillon.activo else 0,
                    sillon.equipamiento,
                ),
            )
        return sillon

    def obtener_por_id(self, tenant_id: str, sillon_id: str) -> Sillon | None:
        cursor = self._conn.execute(
            """
            SELECT id, tenant_id, nombre, activo, equipamiento
            FROM sillones
            WHERE tenant_id = ? AND id = ?;
            """,
            (tenant_id, sillon_id),
        )
        row = cursor.fetchone()
        return self._fila_a_sillon(row) if row else None

    def listar_por_tenant(
        self, tenant_id: str, solo_activos: bool | None = None
    ) -> list[Sillon]:
        filtros = ["tenant_id = ?"]
        params: list[object] = [tenant_id]
        if solo_activos is not None:
            filtros.append("activo = ?")
            params.append(1 if solo_activos else 0)
        where_clause = " AND ".join(filtros)
        cursor = self._conn.execute(
            f"""
            SELECT id, tenant_id, nombre, activo, equipamiento
            FROM sillones
            WHERE {where_clause}
            ORDER BY nombre ASC;
            """,
            tuple(params),
        )
        return [self._fila_a_sillon(row) for row in cursor.fetchall()]

    def obtener_o_crear(self, tenant_id: str, nombre: str) -> Sillon:
        cursor = self._conn.execute(
            """
            SELECT id, tenant_id, nombre, activo, equipamiento
            FROM sillones
            WHERE tenant_id = ? AND nombre = ?;
            """,
            (tenant_id, nombre),
        )
        row = cursor.fetchone()
        if row:
            return self._fila_a_sillon(row)
        sillon = Sillon(nombre=nombre, tenant_id=tenant_id)
        return self.guardar(sillon)


class RepositorioPacientes:
    """Acceso a datos de pacientes filtrados por tenant."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def _fila_a_paciente(self, row: sqlite3.Row) -> Paciente:
        return Paciente(
            id=row["id"],
            tenant_id=row["tenant_id"],
            nombre=row["nombre"],
            dni=row["dni"] or "",
            telefono=row["telefono"] or "",
        )

    def guardar(self, paciente: Paciente) -> Paciente:
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO tenants (id, nombre) VALUES (?, ?);",
                (paciente.tenant_id, paciente.tenant_id),
            )
            self._conn.execute(
                """
                INSERT INTO pacientes (id, tenant_id, nombre, dni, telefono)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    nombre = excluded.nombre,
                    dni = excluded.dni,
                    telefono = excluded.telefono;
                """,
                (
                    paciente.id,
                    paciente.tenant_id,
                    paciente.nombre,
                    paciente.dni,
                    paciente.telefono,
                ),
            )
        return paciente

    def obtener_por_id(self, tenant_id: str, paciente_id: str) -> Paciente | None:
        cursor = self._conn.execute(
            """
            SELECT id, tenant_id, nombre, dni, telefono
            FROM pacientes
            WHERE tenant_id = ? AND id = ?;
            """,
            (tenant_id, paciente_id),
        )
        row = cursor.fetchone()
        return self._fila_a_paciente(row) if row else None

    def listar_por_tenant(
        self,
        tenant_id: str,
        dni: str | None = None,
        nombre: str | None = None,
    ) -> list[Paciente]:
        filtros = ["tenant_id = ?"]
        params: list[str] = [tenant_id]
        if dni is not None and dni.strip():
            filtros.append("LOWER(TRIM(dni)) = ?")
            params.append(dni.strip().lower())
        if nombre is not None and nombre.strip():
            patron = (
                nombre.strip()
                .lower()
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            filtros.append("LOWER(nombre) LIKE ? ESCAPE '\\'")
            params.append(f"%{patron}%")
        where_clause = " AND ".join(filtros)
        cursor = self._conn.execute(
            f"""
            SELECT id, tenant_id, nombre, dni, telefono
            FROM pacientes
            WHERE {where_clause}
            ORDER BY nombre ASC;
            """,
            tuple(params),
        )
        return [self._fila_a_paciente(row) for row in cursor.fetchall()]

    def obtener_o_crear(self, tenant_id: str, nombre: str) -> Paciente:
        cursor = self._conn.execute(
            """
            SELECT id, tenant_id, nombre, dni, telefono
            FROM pacientes
            WHERE tenant_id = ? AND nombre = ?;
            """,
            (tenant_id, nombre),
        )
        row = cursor.fetchone()
        if row:
            return self._fila_a_paciente(row)
        paciente = Paciente(nombre=nombre, tenant_id=tenant_id)
        return self.guardar(paciente)


class RepositorioTurnos:
    """Acceso y persistencia de turnos odontológicos con aislamiento estricto por tenant."""

    _BASE_SELECT = """
        SELECT t.id, t.tenant_id, t.fecha, t.hora_inicio, t.hora_fin, t.estado,
               p.id as prof_id, p.nombre as prof_nombre, p.activo as prof_activo,
               p.matricula as prof_matricula, p.especialidad as prof_especialidad,
               s.id as sil_id, s.nombre as sil_nombre, s.activo as sil_activo,
               s.equipamiento as sil_equipamiento,
               pac.id as pac_id, pac.nombre as pac_nombre, pac.dni as pac_dni
        FROM turnos t
        JOIN profesionales p ON t.profesional_id = p.id
        JOIN sillones s ON t.sillon_id = s.id
        JOIN pacientes pac ON t.paciente_id = pac.id
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._repo_prof = RepositorioProfesionales(conn)
        self._repo_sillon = RepositorioSillones(conn)
        self._repo_pac = RepositorioPacientes(conn)

    def guardar(self, turno: Turno) -> Turno:
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO tenants (id, nombre) VALUES (?, ?);",
                (turno.tenant_id, turno.tenant_id),
            )
            profesional = (
                self._repo_prof.obtener_por_id(turno.tenant_id, turno.profesional.id)
                or self._repo_prof.obtener_o_crear(
                    turno.tenant_id, turno.profesional.nombre
                )
            )
            sillon = (
                self._repo_sillon.obtener_por_id(turno.tenant_id, turno.sillon.id)
                or self._repo_sillon.obtener_o_crear(
                    turno.tenant_id, turno.sillon.nombre
                )
            )
            paciente = (
                self._repo_pac.obtener_por_id(turno.tenant_id, turno.paciente_id)
                if turno.paciente_id
                else None
            ) or self._repo_pac.obtener_o_crear(turno.tenant_id, turno.paciente)

            self._conn.execute(
                """
                INSERT INTO turnos (
                    id, tenant_id, paciente_id, profesional_id, sillon_id,
                    fecha, hora_inicio, hora_fin, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    fecha = excluded.fecha,
                    hora_inicio = excluded.hora_inicio,
                    hora_fin = excluded.hora_fin,
                    estado = excluded.estado;
                """,
                (
                    turno.id,
                    turno.tenant_id,
                    paciente.id,
                    profesional.id,
                    sillon.id,
                    turno.fecha,
                    turno.hora_inicio,
                    turno.hora_fin,
                    turno.estado,
                ),
            )
        return replace(
            turno,
            profesional=profesional,
            sillon=sillon,
            paciente=paciente.nombre,
            paciente_id=paciente.id,
        )

    def actualizar(self, turno: Turno) -> Turno:
        with self._conn:
            self._conn.execute(
                """
                UPDATE turnos
                SET fecha = ?, hora_inicio = ?, hora_fin = ?, estado = ?
                WHERE id = ? AND tenant_id = ?;
                """,
                (
                    turno.fecha,
                    turno.hora_inicio,
                    turno.hora_fin,
                    turno.estado,
                    turno.id,
                    turno.tenant_id,
                ),
            )
        return turno

    def _fila_a_turno(self, row: sqlite3.Row) -> Turno:
        profesional = Profesional(
            id=row["prof_id"],
            tenant_id=row["tenant_id"],
            nombre=row["prof_nombre"],
            activo=bool(row["prof_activo"]),
            matricula=row["prof_matricula"] or "",
            especialidad=row["prof_especialidad"] or "",
        )
        sillon = Sillon(
            id=row["sil_id"],
            tenant_id=row["tenant_id"],
            nombre=row["sil_nombre"],
            activo=bool(row["sil_activo"]),
            equipamiento=row["sil_equipamiento"] or "",
        )
        return Turno(
            id=row["id"],
            tenant_id=row["tenant_id"],
            profesional=profesional,
            sillon=sillon,
            fecha=row["fecha"],
            hora_inicio=row["hora_inicio"],
            hora_fin=row["hora_fin"],
            paciente=row["pac_nombre"],
            estado=row["estado"],
            paciente_id=row["pac_id"],
        )

    def obtener_por_id(self, tenant_id: str, turno_id: str) -> Turno | None:
        cursor = self._conn.execute(
            f"{self._BASE_SELECT} WHERE t.tenant_id = ? AND t.id = ?;",
            (tenant_id, turno_id),
        )
        row = cursor.fetchone()
        return self._fila_a_turno(row) if row else None

    def buscar_activos_por_fecha(self, tenant_id: str, fecha: str) -> list[Turno]:
        cursor = self._conn.execute(
            f"""
            {self._BASE_SELECT}
            WHERE t.tenant_id = ? AND t.fecha = ? AND t.estado IN ('PENDIENTE', 'CONFIRMADO');
            """,
            (tenant_id, fecha),
        )
        return [self._fila_a_turno(row) for row in cursor.fetchall()]

    def listar_por_tenant(
        self,
        tenant_id: str,
        fecha: str | None = None,
        profesional_id: str | None = None,
        sillon_id: str | None = None,
    ) -> list[Turno]:
        filtros = ["t.tenant_id = ?"]
        params: list[str] = [tenant_id]
        if fecha is not None:
            filtros.append("t.fecha = ?")
            params.append(fecha)
        if profesional_id is not None:
            filtros.append("t.profesional_id = ?")
            params.append(profesional_id)
        if sillon_id is not None:
            filtros.append("t.sillon_id = ?")
            params.append(sillon_id)

        where_clause = " AND ".join(filtros)
        cursor = self._conn.execute(
            f"""
            {self._BASE_SELECT}
            WHERE {where_clause}
            ORDER BY t.fecha ASC, t.hora_inicio ASC;
            """,
            tuple(params),
        )
        return [self._fila_a_turno(row) for row in cursor.fetchall()]
