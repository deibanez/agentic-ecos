---
tags: [layer/l0, rules, iac]
created: 2026-08-06
purpose: Conocimiento tribal de traps técnicos (append-only)
---

# IAC_TRAPS — Traps Técnicos del Proyecto

> **Propósito**: Capturar traps técnicos recurrentes (IaC, CI/CD, deploy, datos) con ejemplo mal/bien.
> **Formato**: Secciones numeradas. Append-only. Cada trap: síntoma → causa → fix → origen.

---

## Traps Universales

### 1. `set -e` mata exit codes capturados

**Síntoma**: Script muere silenciosamente cuando un comando retorna exit code != 0.
**Causa**: GitHub Actions corre con `bash -e` (exit on error).
**Fix**: Usar `||` para capturar exit codes no-fatales:
```bash
terraform plan -detailed-exitcode ... || RC=$?   # ← Usar ||
```

### 2. Escritura no atómica → JSON/archivo corrupto

**Síntoma**: Archivos con `}{` concatenados (JSON inválido).
**Causa**: Dos procesos concurrentes intercalan escrituras.
**Fix**: Escribir a temp file + rename (atómico):
```python
tmp = path.with_suffix(".tmp")
tmp.write_text(content)
tmp.rename(path)
```

### 3. "Archivo existe" ≠ "Operativo"

**Síntoma**: Workflow/script reportado como presente pero nunca corre.
**Fix**: Verificar métrica de operatividad (runs > 0, último run exitoso), no file exists.

---

<!-- CUSTOMIZE: Agrega tus traps específicos aquí.
     Dominios sugeridos por preset:
     - **CI/CD**: traps de CI/CD del proyecto
     - **IaC**: traps de IaC del proyecto
     - **Cross-repo**: traps de Cross-repo del proyecto

     Formato de cada trap:
     ### {n}. {Título del trap}
     **Síntoma**: ...
     **Causa**: ...
     **Fix**: ...
     **Origen**: {sesión/fecha}
-->

---

> **Última actualización**: 2026-08-06
