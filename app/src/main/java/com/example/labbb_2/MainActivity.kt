package com.example.labbb_2

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.speech.RecognizerIntent
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material.*
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.google.firebase.database.DataSnapshot
import com.google.firebase.database.DatabaseError
import com.google.firebase.database.FirebaseDatabase
import com.google.firebase.database.ValueEventListener
import java.util.Locale

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val database = FirebaseDatabase.getInstance()

        val startSpeechRecognition = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {
            if (it.resultCode == RESULT_OK && it.data != null) {
                val results = it.data!!.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                val spokenText = results?.get(0).orEmpty()
                processVoiceCommand(spokenText, database)
            }
        }

        setContent {
            MaterialTheme {
                Column(modifier = Modifier.padding(16.dp)) {
                    CoffeeMachineControl(database = database)

                    Button(onClick = {
                        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                        startSpeechRecognition.launch(intent)
                    }) {
                        Text("Voice Command")
                    }
                }
            }
        }

    }

    private fun processVoiceCommand(command: String, database: FirebaseDatabase) {
        when {
            command.contains("turn on coffee machine", ignoreCase = true) -> database.getReference("coffee_machine/status").setValue("on")
            command.contains("turn off coffee machine", ignoreCase = true) -> database.getReference("coffee_machine/status").setValue("off")
            command.contains("make americano", ignoreCase = true) -> {
                database.getReference("coffee_machine/status").setValue("on")
                database.getReference("coffee_machine/type").setValue("Americano")
            }
            command.contains("make latte", ignoreCase = true) -> {
                database.getReference("coffee_machine/status").setValue("on")
                database.getReference("coffee_machine/type").setValue("Latte")
            }
            command.contains("make cappuccino", ignoreCase = true) -> {
                database.getReference("coffee_machine/status").setValue("on")
                database.getReference("coffee_machine/type").setValue("Cappuccino")
            }
        }
    }


    @Composable
    fun CoffeeMachineControl(database: FirebaseDatabase) {
        // 咖啡机状态和类型
        var status by remember { mutableStateOf(false) }
        var type by remember { mutableStateOf("") }

        val coffeeMachineRef = database.getReference("coffee_machine")
        coffeeMachineRef.addValueEventListener(object : ValueEventListener {
            override fun onDataChange(snapshot: DataSnapshot) {
                status = snapshot.child("status").getValue(String::class.java) == "on"
                type = snapshot.child("type").getValue(String::class.java).orEmpty()
            }
            override fun onCancelled(error: DatabaseError) {}
        })

        Column(modifier = Modifier.padding(16.dp)) {
            // 显示咖啡机状态
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(text = "Coffee Machine Status: ", modifier = Modifier.weight(1f))
                Switch(
                    checked = status,
                    onCheckedChange = { isOn ->
                        status = isOn
                        coffeeMachineRef.child("status").setValue(if (isOn) "on" else "off")
                    }
                )
            }

            // 显示咖啡类型
            Text("Coffee Type: $type")

            // 选择咖啡类型的按钮纵向排列
            Column {
                CoffeeTypeButton("Americano", onClick = { coffeeMachineRef.child("type").setValue("Americano") })
                Spacer(modifier = Modifier.height(8.dp))
                CoffeeTypeButton("Latte", onClick = { coffeeMachineRef.child("type").setValue("Latte") })
                Spacer(modifier = Modifier.height(8.dp))
                CoffeeTypeButton("Cappuccino", onClick = { coffeeMachineRef.child("type").setValue("Cappuccino") })
            }
        }
    }

    @Composable
    fun CoffeeTypeButton(buttonText: String, onClick: () -> Unit) {
        Button(
            onClick = onClick,
            modifier = Modifier
                .fillMaxWidth()
                .height(48.dp) // 你可以根据需要调整高度
        ) {
            Text(buttonText)
        }
    }


}