from odoo.upgrade import util

def pre_init_hook(env):
    required_modules = "l10n_fr_ecotaxe"
    if not env["ir.module.module"].search([("name", "=", required_modules)]):
        return

    updates = [
        # account.move
        ("account.move", "amount_ecotaxe", "amount_ecotax"),
        # account.move.line
        ("account.move.line", "subtotal_ecotaxe", "subtotal_ecotax"),
        ("account.move.line", "unit_ecotaxe_amount", "ecotax_amount_unit"),
        # product.template
        ("product.template", "ecotaxe_amount", "ecotax_amount"),
        # account.ecotaxe.classification
        ("account.ecotaxe.classification", "ecotaxe_type", "ecotax_type"),
        ("account.ecotaxe.classification", "ecotaxe_coef", "ecotax_coef"),
        (
            "account.ecotaxe.classification",
            "default_fixed_ecotaxe",
            "default_fixed_ecotax",
        ),
        ("account.ecotaxe.classification", "account_ecotaxe_categ_id", "categ_id"),
        (
            "account.ecotaxe.classification",
            "ecotaxe_product_status",
            "product_status",
        ),
        (
            "account.ecotaxe.classification",
            "ecotaxe_supplier_status",
            "supplier_status",
        ),
        ("account.ecotaxe.classification", "ecotaxe_deb_code", "emebi_code"),
        ("account.ecotaxe.classification", "ecotaxe_scale_code", "scale_code"),
        # Rename model
        ("account.ecotaxe.category", None, "account.ecotax.category"),
        ("account.ecotaxe.classification", None, "account.ecotax.classification"),
    ]

    column_renames = []
    model_renames = []

    for model, old_val, new_val in updates:
        model_db_name = model.replace(".", "_")
        if old_val:
            if util.column_exists(env.cr, model_db_name, old_val):
                column_renames.append((model, old_val, new_val))
        else:
            model_renames.append((model, new_val))

    if column_renames:
        for line in column_renames:
            util.rename_field(env.cr, *line)

    if model_renames:
        for line in model_renames:
            util.rename_model(env.cr, *line)


def post_init_hook(env):
    env.cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'product_template'
          AND column_name IN ('ecotaxe_classification_id', 'manual_fixed_ecotaxe')
    """)
    fields = [row[0] for row in env.cr.fetchall()]
    if all(field in fields for field in ['ecotaxe_classification_id', 'manual_fixed_ecotaxe']):

        env.cr.execute("""
            SELECT id, ecotaxe_classification_id, manual_fixed_ecotaxe
            FROM product_template
            WHERE ecotaxe_classification_id IS NOT NULL
            OR manual_fixed_ecotaxe IS NOT NULL
        """)
        templates = env.cr.fetchall()

        ecotax_product = env["ecotax.line.product"]
        for template_id, classification_id, force_amount in templates:
            vals = {
                "product_tmpl_id": template_id,
                "classification_id": classification_id,
                "force_amount": force_amount,
            }
            record = ecotax_product.create(vals)
            template = env["product.template"].browse(template_id)
            template.write({"ecotax_line_product_ids": [(4, record.id)]})

    if not env["ir.module.module"].search([("name", "=", "l10n_fr_ecotaxe")]):
        return

    util.remove_module(env.cr, "l10n_fr_ecotaxe")
