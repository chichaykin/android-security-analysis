package org.maxresearch.probe;

import android.app.Activity;
import android.app.Instrumentation;
import android.graphics.Rect;
import android.os.Bundle;
import android.os.SystemClock;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.app.UiAutomation;
import android.view.accessibility.AccessibilityNodeInfo;
import android.util.Xml;
import java.io.StringWriter;
import java.util.List;
import org.xmlpull.v1.XmlSerializer;

/** Read the active tree, or fill one explicitly selected MAX input field. */
public final class Probe extends Instrumentation {
    private Bundle arguments;
    @Override public void onCreate(Bundle arguments) {
        super.onCreate(arguments);
        this.arguments = arguments == null ? new Bundle() : new Bundle(arguments);
        start();
    }

    @Override public void onStart() {
        Bundle result = new Bundle();
        try {
            UiAutomation automation = getUiAutomation();
            AccessibilityServiceInfo info = automation.getServiceInfo();
            info.flags |= AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS;
            automation.setServiceInfo(info);
            AccessibilityNodeInfo root = null;
            for (int attempt = 0; attempt < 50 && root == null; attempt++) {
                root = automation.getRootInActiveWindow();
                if (root == null) SystemClock.sleep(100);
            }
            if (root == null) throw new IllegalStateException("No active accessibility root");
            if ("fill".equals(arguments.getString("mode"))) {
                String id = arguments.getString("resource_id", "");
                String value = arguments.getString("value");
                if (!id.startsWith("ru.oneme.app:id/") || value == null || value.length() > 4096)
                    throw new IllegalArgumentException("Invalid explicitly selected input");
                List<AccessibilityNodeInfo> matches = root.findAccessibilityNodeInfosByViewId(id);
                if (matches.size() != 1) throw new IllegalStateException("Input selector is not unique");
                AccessibilityNodeInfo field = matches.get(0);
                if (!field.isEnabled() || !field.isEditable() || !"ru.oneme.app".equals(text(field.getPackageName())))
                    throw new IllegalStateException("Selected node is not an enabled MAX input");
                Bundle action = new Bundle();
                action.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, value);
                if (!field.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, action))
                    throw new IllegalStateException("Input action failed");
                result.putString("input_result", "filled");
                finish(Activity.RESULT_OK, result);
                return;
            }
            StringWriter output = new StringWriter();
            XmlSerializer xml = Xml.newSerializer();
            xml.setOutput(output);
            xml.startTag(null, "hierarchy");
            writeNode(xml, root, 0);
            xml.endTag(null, "hierarchy");
            xml.flush();
            result.putString("hierarchy", output.toString());
            finish(Activity.RESULT_OK, result);
        } catch (Exception error) {
            result.putString("error", error.getClass().getSimpleName() + ": " + error.getMessage());
            finish(Activity.RESULT_CANCELED, result);
        }
    }

    private static String text(CharSequence value) {
        return value == null ? "" : value.toString();
    }

    private static void writeNode(XmlSerializer xml, AccessibilityNodeInfo node, int depth) throws Exception {
        if (depth > 80) throw new IllegalStateException("Accessibility tree exceeded depth limit");
        Rect bounds = new Rect();
        node.getBoundsInScreen(bounds);
        xml.startTag(null, "node");
        xml.attribute(null, "resource-id", text(node.getViewIdResourceName()));
        xml.attribute(null, "package", text(node.getPackageName()));
        xml.attribute(null, "class", text(node.getClassName()));
        xml.attribute(null, "text", text(node.getText()));
        xml.attribute(null, "content-desc", text(node.getContentDescription()));
        xml.attribute(null, "clickable", Boolean.toString(node.isClickable()));
        xml.attribute(null, "enabled", Boolean.toString(node.isEnabled()));
        xml.attribute(null, "bounds", "[" + bounds.left + "," + bounds.top + "][" + bounds.right + "," + bounds.bottom + "]");
        for (int index = 0; index < node.getChildCount(); index++) {
            AccessibilityNodeInfo child = node.getChild(index);
            if (child != null) writeNode(xml, child, depth + 1);
        }
        xml.endTag(null, "node");
    }
}
