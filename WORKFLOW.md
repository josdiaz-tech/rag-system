# WORKFLOW

## 1. ¿Por qué cualquiera puede registrarse sin restricción?

**Sí, es porque estamos en MVP.** Hay varias razones:

### Estado actual (MVP)

- **Registro abierto** - Cualquiera puede crear cuenta
- **Sin verificación de email** - No hay confirmación
- **Sin invitaciones** - No se requiere código de invitación
- **Sin aprobación manual** - Auto-activado al registrar

### Por qué se hizo así para MVP

- ✅ Más rápido para desarrollo/testing
- ✅ Más fácil para demos con el cliente
- ✅ No requiere servicio de email (SendGrid, etc.)
- ✅ Permite testing multi-usuario inmediato

### Para PRODUCCIÓN deberías considerar

1. **Registro por invitación** - Admin genera códigos de invitación
2. **Verificación de email** - Confirmar email antes de activar
3. **Aprobación manual** - Admin revisa y aprueba cada registro
4. **Whitelist de dominios** - Solo emails @tuempresa.com
5. **Desactivar registro público** - Solo admin puede crear usuarios

---

## 2. ¿Por qué no hay admin por defecto?

**Gran observación - esto es un hueco de seguridad.**

### El problema actual

```python
# En database.py
class User:
    is_admin = Column(Boolean, default=False)
```

- ❌ **No hay admin inicial** - Nadie tiene privilegios admin
- ❌ **No hay forma de crear admin** - No hay endpoint para promover usuarios
- ❌ **No hay seed data** - No se crea admin al inicializar DB

### Consecuencias

- Todos los usuarios son iguales (usuarios normales)
- El campo `is_admin` existe pero nunca se usa
- No hay forma de hacer tareas administrativas

### Soluciones típicas

#### **Opción 1: Admin por defecto en primera ejecución**

```text
Si la tabla users está vacía:
  → Crear usuario admin@empresa.com con contraseña temporal
  → Obligar a cambiar contraseña en primer login
```

#### **Opción 2: Comando de consola**

```bash
python manage.py create-admin --email admin@empresa.com
```

#### **Opción 3: Variable de entorno**

```bash
# .env
ADMIN_EMAIL=admin@empresa.com
ADMIN_PASSWORD=temporal123!

# Al iniciar app, verificar si existe, si no, crear
```

#### **Opción 4: Promoción manual en DB**

```sql
UPDATE users SET is_admin = true WHERE email = 'jose@empresa.com';
```

---

## 3. ¿Se puede ajustar para que solo admin suba archivos y los comparta?

**SÍ, es totalmente posible, pero requiere cambios significativos en la arquitectura.**

### Arquitectura actual (Multi-tenant aislado)

```text
User 1 → Documents 1 → Queries 1
User 2 → Documents 2 → Queries 2
User 3 → Documents 3 → Queries 3

❌ Los usuarios NO pueden ver documentos de otros
```

### Arquitectura que necesitarías (Compartida con permisos)

#### **Modelo A: Documentos globales (más simple)**

```text
Admin → Sube documentos
       ↓
    [Document Pool Global]
       ↓
Todos los usuarios pueden hacer queries sobre TODOS los documentos
```

**Cambios necesarios:**

- ✅ Relativamente fácil
- Quitar filtro `user_id` en queries
- Mantener filtro `user_id` en uploads (solo admin)
- Verificar `is_admin` en endpoint de upload

**Problema:** No hay privacidad entre usuarios

---

#### **Modelo B: Permisos por documento (más complejo)**

```text
Admin sube Documento A → Asigna a [User1, User2]
Admin sube Documento B → Asigna a [User2, User3]

User1 puede ver: Documento A
User2 puede ver: Documento A, B
User3 puede ver: Documento B
```

**Cambios necesarios:**

- Nueva tabla: `document_permissions`

  ```sql
  document_id | user_id | permission_type
  uuid-123   | 1       | read
  uuid-123   | 2       | read
  ```

- Modificar queries de vectores para filtrar por permisos
- UI para que admin asigne permisos
- Endpoints para gestionar permisos

**Impacto:** Significativo pero limpio

---

#### **Modelo C: Grupos/Departamentos (enterprise)**

```text
Admin crea grupos: "Técnicos", "Managers", "Todos"
Admin sube docs y asigna a grupos
Users pertenecen a uno o más grupos
```

**Cambios necesarios:**

- Tabla `groups`
- Tabla `user_groups` (many-to-many)
- Tabla `document_groups` (many-to-many)
- Lógica compleja de permisos

**Impacto:** Grande, pero escalable

---

### ¿Se rompería todo?

**Depende del modelo:**

#### Modelo A (Global): ⚠️ **Cambios medianos**

- ✅ Base de datos: Sin cambios
- ✅ Backend: Cambios pequeños en filtros
- ✅ Vector store: Cambios en queries (quitar filtro user_id)
- ⚠️ Frontend: Pequeños cambios en UI
- **Tiempo estimado:** 1-2 días

#### Modelo B (Permisos): 🔶 **Cambios significativos**

- 🔶 Base de datos: Nueva tabla + migraciones
- 🔶 Backend: Nueva lógica de permisos
- 🔶 Vector store: Filtros más complejos
- 🔶 Frontend: UI de gestión de permisos
- **Tiempo estimado:** 1 semana

#### Modelo C (Grupos): 🔴 **Re-arquitectura parcial**

- 🔴 Base de datos: Múltiples tablas nuevas
- 🔴 Backend: Sistema completo de ACL
- 🔴 Vector store: Queries complejas
- 🔴 Frontend: UI administrativa completa
- **Tiempo estimado:** 2-3 semanas

---

## Mi recomendación para el cliente

### Para este proyecto (telecomunicaciones FTTH)

**Escenario 1: Intranet pequeña (<50 usuarios)**
→ **Modelo A (Global)** es suficiente

- Admin sube manuales técnicos
- Todos los técnicos pueden consultar
- Sin necesidad de privacidad entre usuarios

**Escenario 2: Múltiples departamentos**
→ **Modelo B (Permisos)** es ideal

- Admin/Managers suben docs específicos
- Algunos docs son generales, otros privados
- Control granular

**Escenario 3: Empresa grande/múltiples clientes**
→ **Modelo C (Grupos)** es necesario

- Escalabilidad
- Auditoría completa
- Multi-tenancy real

---

## ¿Qué hacer AHORA para producción?

### Prioridades inmediatas

1. **Crear admin inicial** (Opción 3: variable de entorno)
2. **Decidir modelo de permisos con el cliente**
3. **Si eligen Modelo A:** Implementar en 1-2 días
4. **Si eligen Modelo B:** Planificar para post-MVP
5. **Cerrar registro público o agregar whitelist de emails**

### Preguntas para el cliente

1. ¿Cuántos usuarios totales esperan? (<10, <50, <100, 100+)
2. ¿Todos deben ver todos los documentos? (Sí → Modelo A)
3. ¿Necesitan privacidad por departamento? (Sí → Modelo B)
4. ¿Es para una sola empresa o múltiples clientes? (Múltiples → Modelo C)
5. ¿Quién debe poder subir documentos? (Solo admin vs. roles específicos)

---
